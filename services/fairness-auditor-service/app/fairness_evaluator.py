from db import get_connection
from models import FARequest
from logger import logger
import json
from datetime import datetime
import uuid

def evaluate_fairness(request: FARequest) -> dict:
    logger.info(f"Evaluating Fairness user {request.user_id}, ml_result_id {request.ml_result_id}")
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Step 1: Fetch shap_summary from ml_prediction_results
        cur.execute("""
            SELECT shap_summary FROM ml_prediction_results  
            WHERE id = %s
        """, (request.ml_result_id,))

        row = cur.fetchone()
        if not row:
            raise Exception("result not found.")

        shap_summary = row[0]  # JSONB from Postgres
        logger.info(f"kkkkk")
        logger.info(f"Fetched shap_summary for fairness audit: {shap_summary}")

        # Step 2: Based on the SHAP summary, Evaluate Fairness
        biased_features = {}
        bias_threshold = 0.3  # Example threshold
        for feature, impact in shap_summary.items():
            if abs(impact) > bias_threshold:
                biased_features[feature] = f"Impact: {impact}"
        
        is_biased = len(biased_features) > 0
        audit_notes = "Bias detected in features." if is_biased else "No significant bias detected."
        logger.info(f"Fairness Audit Result: is_biased={is_biased}, flagged_features={biased_features}")
        
        # Step 3: Insert into fairness_audit_log
        audit_result_id = str(uuid.uuid4())
        audited_at = datetime.now()
        cur.execute("""
            INSERT INTO fairness_audit_log (id, ml_result_id, bias_detected, flagged_fields, audit_summary, audited_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            audit_result_id,
            request.ml_result_id,
            is_biased,
            json.dumps(biased_features),
            audit_notes,
            audited_at
        ))
        
        conn.commit()
        logger.info(f"Inserted Fairness Audit log {audit_result_id}")

        return {
            "is_biased": is_biased,
            "flagged_features": biased_features,
            "audit_notes": audit_notes,
            "audit_result_id": audit_result_id
        }

    except Exception as e:
        logger.error(f"Error in evaluate_ml: {e}")
        raise
    finally:
        cur.close()
        conn.close()

