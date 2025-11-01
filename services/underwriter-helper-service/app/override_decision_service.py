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
        logger.info(f"Validating underwriter with ID {request.underwriter_id}")
        cur.execute("""
            SELECT role FROM users WHERE id = %s
        """, (request.underwriter_id,))
        user = cur.fetchone()

        if not user or user[0].lower() != 'underwriter':
            raise Exception("Permission denied: Only users with 'underwriter' role can update decisions.")
        
        logger.info(f"Underwriter {request.underwriter_id} is authorized to update decisions.")

        # Step 2: Fetch latest decision for borrower
        cur.execute("""
            SELECT id, final_decision, ml_result_id, rule_result_id, fairness_audit_log_id, explanation, type
            FROM decision_log 
            WHERE borrower_id = %s 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (request.borrower_id,))
        row = cur.fetchone()
        logger.info(f"Fetched latest decision log for borrower {request.borrower_id}: {row}")

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
        logger.info(f"Underwriter {request.underwriter_id} manually updated decision for borrower {request.borrower_id} to '{request.new_status}'")

        # Step 5: Add training data based on overridden decision
        cur.execute("""
            SELECT parsed_data FROM documents 
            WHERE user_id = %s
            ORDER BY uploaded_at DESC 
            LIMIT 1
        """, (request.borrower_id,))
        doc_row = cur.fetchone()
        if not doc_row:
            raise Exception("Borrower document not found to extract features for training.")

        parsed_data = doc_row[0]  # Assumes JSONB dict from DB
        logger.info(f"Parsed data for training: {parsed_data}")

        # Clean and extract numeric values
        salary = float(parsed_data["annual_salary"].replace("$", "").replace(",", "").strip())
        credit_score = int(parsed_data["credit_score"])
        employment_years = int(parsed_data["employment_years"])
        loan_amount = float(parsed_data["loan_amount"].replace("$", "").replace(",", "").strip())

        target = 1 if request.new_status.lower() == "approved" else 0

        logger.info(f"Appending training data: salary={salary}, credit_score={credit_score}, employment_years={employment_years}, loan_amount={loan_amount}, target={target}")

        cur.execute("""
            INSERT INTO training_data (id, salary, credit_score, employment_years, loan_amount, target)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            str(uuid.uuid4()),
            salary,
            credit_score,
            employment_years,
            loan_amount,
            target
        ))
        conn.commit()
        logger.info(f"Appended training data due to underwriter override: borrower {request.borrower_id}, target {target}")

        logger.info(f"Manual decision update completed successfully for borrower {request.borrower_id}")

        return {"message": f"Status successfully updated to '{request.new_status}'", "new_decision_id": new_decision_id}

    except Exception as e:
        logger.error(f"Manual update failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        conn.close()     