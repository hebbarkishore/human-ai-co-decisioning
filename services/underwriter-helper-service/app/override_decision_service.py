from db import get_connection
from logger import logger
import json
import uuid
from datetime import datetime
from fastapi import HTTPException
from models import ManualDecisionUpdateRequest

def update_decision_by_underwriter(request: ManualDecisionUpdateRequest):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Step 1: Validate underwriter
        cur.execute("""
            SELECT role FROM users WHERE id = %s
        """, (request.underwriter_id,))
        user = cur.fetchone()

        if not user or user[0].lower() != 'underwriter':
            raise Exception("Permission denied: Only users with 'underwriter' role can update decisions.")

        # Step 2: Fetch latest decision for borrower
        cur.execute("""
            SELECT id, final_decision, ml_result_id, rule_result_id, fairness_audit_log_id, explanation, type
            FROM decision_log 
            WHERE borrower_id = %s 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (request.borrower_id,))
        row = cur.fetchone()

        if not row:
            raise Exception("No decision record found for borrower.")

        latest_decision_id, current_status, ml_id, rule_id, audit_id, explanation, typ = row

        # Step 3: Check if status already matches
        if current_status.lower() == request.new_status.lower():
            return {"message": f"Status is already '{current_status}'"}

        # Step 4: Insert new decision log
        new_decision_id = str(uuid.uuid4())
        now = datetime.now()

        cur.execute("""
            INSERT INTO decision_log (
                id, borrower_id, final_decision, ml_result_id, rule_result_id, fairness_audit_log_id,
                explanation, type, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            new_decision_id,
            request.borrower_id,
            request.new_status.lower(),
            ml_id,
            rule_id,
            audit_id,
            "Updated by underwriter",
            "override",
            now
        ))

        conn.commit()
        logger.info(f"Underwriter {request.underwriter_id} manually updated decision for borrower {request.borrower_id} to '{request.new_status}'")

        return {"message": f"Status successfully updated to '{request.new_status}'", "new_decision_id": new_decision_id}

    except Exception as e:
        logger.error(f"Manual update failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        conn.close()     