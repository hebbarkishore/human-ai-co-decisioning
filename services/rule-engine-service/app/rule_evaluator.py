from db import get_connection
from models import RuleRequest, RuleResult
from logger import logger
import json
from datetime import datetime
import uuid


def evaluate_rules(request: RuleRequest) -> dict:
    logger.info(f"🔍 Evaluating rules for user {request.user_id}, document {request.document_id}")
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Step 1: Fetch parsed_data from documents
        cur.execute("""
            SELECT parsed_data FROM documents 
            WHERE id = %s AND user_id = %s
        """, (request.document_id, request.user_id))

        row = cur.fetchone()
        if not row:
            raise Exception("Document not found.")

        parsed_data = row[0]  # JSONB from Postgres

        logger.info(f"Fetched parsed data for rule evaluation: {parsed_data}")

        # Step 2: Fetch all active rules
        cur.execute("SELECT name, field, operator, value, message FROM rules_config")
        rules = cur.fetchall()

        reasons = {}
        passed = True

        for rule in rules:
            name, field, operator, expected_value, message = rule
            actual_value = parsed_data.get(field)

            if actual_value is None:
                reasons[name] = f"Skipped: {field} not found in document"
                continue

            result = evaluate_condition(actual_value, operator, expected_value)

            if result:
                reasons[name] = "Passed"
            else:
                passed = False
                reasons[name] = f"Failed: {message or f'{field} {operator} {expected_value}'}"

        # Step 3: Insert into rule_evaluation_log
        rule_result_id = str(uuid.uuid4())
        rule_status = "pass" if passed else "fail"
        evaluated_at = datetime.now()

        cur.execute("""
            INSERT INTO rule_evaluation_log (id, user_id, document_id, rule_values, rule_status, evaluated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            rule_result_id,
            request.user_id,
            request.document_id,
            json.dumps(reasons),
            rule_status,
            evaluated_at
        ))

        conn.commit()
        logger.info(f"Inserted rule log {rule_result_id}")

        return {
            "status": rule_status,
            "reasons": reasons,
            "rule_result_id": rule_result_id
        }

    except Exception as e:
        logger.error(f"Error in evaluate_rules: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def evaluate_condition(actual, operator, expected):
    try:
        def clean_number(val):
            if isinstance(val, str):
                val = val.replace("$", "").replace(",", "").strip()
            return val
        
        actual = clean_number(actual)
        expected = clean_number(expected)
        if operator in [">", ">=", "<", "<="]:
            actual = float(actual)
            expected = float(expected)

        if operator == ">":
            return actual > expected
        elif operator == ">=":
            return actual >= expected
        elif operator == "<":
            return actual < expected
        elif operator == "<=":
            return actual <= expected
        elif operator == "=":
            return str(actual).lower() == str(expected).lower()
        elif operator == "!=":
            return str(actual).lower() != str(expected).lower()
        elif operator == "in":
            return str(actual).lower() in [e.strip().lower() for e in expected.split(",")]
        elif operator == "not in":
            return str(actual).lower() not in [e.strip().lower() for e in expected.split(",")]
        else:
            return False
    except Exception as e:
        logger.warning(f"Error evaluating rule {operator} on {actual} vs {expected}: {e}")
        return False