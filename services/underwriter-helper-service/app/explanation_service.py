from db import get_connection
from logger import logger
import json
from fastapi import HTTPException
from models import ExplanationResponse, ExplanationDetails, ExplanationWithCases, ManualDecisionUpdateRequest

def explain_borrower_application(user_id: str):
    logger.info(f"Generating explanation for borrower {user_id}")
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Step 1: Get decision record
        cur.execute("""
            SELECT final_decision, ml_result_id, rule_result_id, fairness_audit_log_id 
            FROM decision_log 
            WHERE borrower_id = %s ORDER BY created_at DESC LIMIT 1 
        """, (user_id,))
        decision_row = cur.fetchone()
        if not decision_row:
            raise Exception("Decision log not found for user.")

        final_decision, ml_result_id, rule_result_id, audit_id = decision_row
        logger.info(f"Decision fetched: {final_decision}, ML Result ID: {ml_result_id}, Rule Result ID: {rule_result_id}, Audit ID: {audit_id}")

        # Step 2: Get rule evaluation result
        cur.execute("""
            SELECT rule_status, rule_values 
            FROM rule_evaluation_log 
            WHERE id = %s
        """, (rule_result_id,))
        rule_row = cur.fetchone()
        rule_status = rule_row[0]
        rule_values = rule_row[1] if isinstance(rule_row[1], dict) else json.loads(rule_row[1])
        logger.info(f"rule_evaluation fetched:" f" Status: {rule_status}, Values: {rule_values}")

        # Step 3: Get ML prediction result
        cur.execute("""
            SELECT predicted_decision, confidence_score, shap_summary 
            FROM ml_prediction_results 
            WHERE id = %s
        """, (ml_result_id,))
        ml_row = cur.fetchone()
        predicted_decision = ml_row[0]
        confidence_score = ml_row[1]
        shap_summary = ml_row[2] if isinstance(ml_row[2], dict) else json.loads(ml_row[2])
        logger.info(f"ML prediction fetched:" f" Predicted Decision: {predicted_decision}, Confidence Score: {confidence_score}, SHAP Summary: {shap_summary}")

        # Step 4: Get Fairness audit
        cur.execute("""
            SELECT bias_detected, audit_summary 
            FROM fairness_audit_log 
            WHERE id = %s
        """, (audit_id,))
        audit_row = cur.fetchone()
        bias_detected, audit_summary = audit_row

        logger.info(f"Fairness audit fetched:" f" Bias Detected: {bias_detected}, Audit Summary: {audit_summary}")

        # Prepare explanations
        status = final_decision.lower()

        rule_factors_passed = [k for k, v in rule_values.items() if v.lower().startswith("passed")]
        ml_factors_passed = [k for k, v in shap_summary.items() if v > 0]
        rule_factors_failed = [k for k, v in rule_values.items() if not v.lower().startswith("passed")]
        ml_factors_failed = [k for k, v in shap_summary.items() if v < 0]


        rule_positive_explanation = f"{', '.join(rule_factors_passed)}"
        ml_positive_explanation = f"ML model predicted confidence score of {confidence_score}. " \
                             f"Best positive contributors were: {', '.join(ml_factors_passed)}"
        
        rule_failed_explanation = f"{', '.join(rule_factors_failed)}"
        ml_failed_explanation = f"Key failed contributors were: {', '.join(ml_factors_failed)}"


        fairness_explanation = f"Fairness bias {bias_detected} and audit result: {audit_summary}"

        rule_explanation = ExplanationWithCases(
            passed_cases=rule_positive_explanation,
            failed_cases=rule_failed_explanation,
            result=rule_status
        )

        ml_explanation = ExplanationWithCases(
            passed_cases=ml_positive_explanation,
            failed_cases=ml_failed_explanation,
            result=predicted_decision
        )

        explanation = ExplanationResponse(
            status=status,
            explanation=ExplanationDetails(
                rule_explanation=rule_explanation,
                ml_explanation=ml_explanation,
                fairness_explanation=fairness_explanation
            )
        )
        logger.info(f"Explanation generated for borrower {user_id}: {explanation}")
        return explanation

    except Exception as e:
        logger.error(f"Error in explanation generation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()