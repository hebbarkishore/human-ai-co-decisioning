from logger import logger
import os
import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

import httpx
from db import get_connection  # your DB helper that returns psycopg2 connection


RULE_ENGINE_URL = os.getenv("RULE_ENGINE_URL", "http://rule-engine-service:8000")
ML_DECISION_SERVICE_URL = os.getenv("ML_DECISION_SERVICE_URL", "http://ml-decision-service:8000")  
FIARNESS_AUDITOR_SERVICE_URL = os.getenv("FAIRNESS_AUDITOR_SERVICE_URL", "http://fairness-auditor-service:8000")
CALL_TIMEOUT_SECONDS = 5.0
MAX_WORKERS = 2


def call_rule_engine_sync(user_id: str, document_id: str) -> dict:
    """Sync HTTP call to rule engine. Returns parsed JSON or raises."""
    try:
        with httpx.Client(timeout=CALL_TIMEOUT_SECONDS) as client:
            resp = client.post(
                f"{RULE_ENGINE_URL}/evaluate-rules",
                json={"user_id": user_id, "document_id": document_id},
                timeout=CALL_TIMEOUT_SECONDS
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.exception("Rule engine call failed")
        raise


def call_ml_engine_sync(user_id: str, document_id: str) -> dict:
    """Sync call to ML engine (currently a placeholder). Replace with actual call if available."""
    try:
        with httpx.Client(timeout=CALL_TIMEOUT_SECONDS) as client:
            resp = client.post(
                f"{ML_DECISION_SERVICE_URL}/evaluate-ml-decision",
                json={"user_id": user_id, "document_id": document_id},
                timeout=CALL_TIMEOUT_SECONDS
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.exception("ML decision api call failed")
        raise

def call_fairness_auditor(user_id: str, ml_result_id: str) -> dict:
    """Sync call to Fairness Auditor"""
    try:
        with httpx.Client(timeout=CALL_TIMEOUT_SECONDS) as client:
            resp = client.post(
                f"{FIARNESS_AUDITOR_SERVICE_URL}/fairness-auditor",
                json={"user_id": user_id, "ml_result_id": ml_result_id},
                timeout=CALL_TIMEOUT_SECONDS
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.exception("fairness auditor api call failed")
        raise    
    

def _insert_decision(borrower_id: str, document_id: str, final_decision: str, explanation: str, rule_result_id: str = None,
    ml_result_id: str = None, audit_result_id: str = None):
    """Insert a record into decision_log. Adjust columns to match your DB schema if needed."""
    conn = None
    cur = None
    logger.info("Inserting decision log: %s / %s / %s", borrower_id, rule_result_id, ml_result_id)
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO decision_log (
                type, borrower_id, document_id, final_decision, explanation, rule_result_id, ml_result_id, fairness_audit_log_id, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                "auto",
                borrower_id,
                document_id,
                final_decision,
                explanation,
                rule_result_id,
                ml_result_id,
                audit_result_id,
                datetime.now()
            )
        )
        conn.commit()
        logger.info("Decision log inserted: %s / %s", borrower_id, final_decision)
    except Exception as e:
        logger.exception("Failed to insert decision_log: %s", e)
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def _handle_both_results_and_persist(user_id: str, document_id: str, rule_result: dict, ml_result: dict, fairness_result: dict) -> dict:
    """Decision logic and store final decision."""
    logger.info("rule_result is %s", rule_result)
    rule_status = (rule_result or {}).get("status")  # expect 'pass'/'fail'
    rule_result_id = (rule_result or {}).get("rule_result_id")
    ml_status = (ml_result or {}).get("status")  # expect 'accepted'/'decline' etc
    ml_result_id = (ml_result or {}).get("ml_result_id")
    is_biased = (fairness_result or {}).get("is_biased", False)
    audit_result_id = (fairness_result or {}).get("audit_result_id")

    logger.info("Rule status: %s, ML status: %s, is_biased: %s", rule_status, ml_status, is_biased)

    if is_biased:
        final = "pending_biased"
    else:
        if rule_status == "pass" and ml_status == "accepted":
            final = "approved"
        elif rule_status == "fail" and ml_status == "rejected":
            final = "rejected"
        else:
            final = "pending_conflict"

    explanation = json.dumps({"rule": rule_result, "ml": ml_result})
    _insert_decision(user_id, document_id, final, explanation, rule_result_id, ml_result_id, audit_result_id)
    return {"final_decision": final, "explanation": explanation}

def handle_decision_request(user_id: str, document_id: str):
    """
    Main synchronous entry point.
    Runs rule and ML calls in parallel using ThreadPoolExecutor and waits for both (with timeout).
    On timeout or error, inserts an 'error' decision log.
    """
    logger.info("Starting decision pipeline for user %s, document %s", user_id, document_id)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_name = {
            executor.submit(call_rule_engine_sync, user_id, document_id): "rule",
            executor.submit(call_ml_engine_sync, user_id, document_id): "ml"
        }

        rule_result = None
        ml_result = None

        try:
            # Wait for both futures to complete, enforce total timeout by joining with timeout
            for future in as_completed(future_to_name.keys(), timeout=CALL_TIMEOUT_SECONDS):
                name = future_to_name[future]
                try:
                    result = future.result()  # may raise exception from call
                    if name == "rule":
                        rule_result = result
                    elif name == "ml":
                        ml_result = result
                except Exception as exc:
                    # If one of the calls raises, log and persist error decision
                    logger.exception("%s task failed: %s", name, exc)
                    _insert_decision(user_id, document_id, final_decision="error",
                                     explanation=f"{name} service error: {str(exc)}")
                    return {"status": "error", "reason": f"{name} service error", "detail": str(exc)}

            # After as_completed loop, check if both results collected
            if rule_result is None or ml_result is None:
                # Either timed out or not produced both results
                logger.error("Timeout or missing result - rule: %s, ml: %s", bool(rule_result), bool(ml_result))
                _insert_decision(user_id, document_id, final_decision="error",
                                 explanation="server error: timedout or missing response")
                return {"status": "error", "reason": "timeout_or_missing", "rule_result": rule_result, "ml_result": ml_result}

            # Both results present — perform decision logic and persist
            fairness_result = call_fairness_auditor(user_id, ml_result.get("ml_result_id"))
            decision_summary = _handle_both_results_and_persist(user_id, document_id, rule_result, ml_result, fairness_result)
            logger.info("Final decision recorded: %s", decision_summary["final_decision"])
            return {"status": "ok", **decision_summary}

        except FuturesTimeoutError:
            logger.exception("⏰ Overall timeout waiting for services")
            _insert_decision(user_id, document_id, final_decision="error",
                             explanation="server error: timedout")
            return {"status": "error", "reason": "timeout"}
        except Exception as e:
            logger.exception("Unexpected exception in handle_decision_request: %s", e)
            _insert_decision(user_id, document_id, final_decision="error",
                             explanation=f"server error: {str(e)}")
            return {"status": "error", "reason": "exception", "detail": str(e)}            