from db import get_connection
from models import UserCreate, UserRead
from logger import logger
import os
import httpx
from fastapi import HTTPException

role = "underwriter"
ML_DECISION_SERVICE_URL = os.getenv("ML_DECISION_SERVICE_URL", "http://ml-decision-service:8000")  
EXPLANATION_LETTER_SERVICE_URL = os.getenv("EXPLANATION_LETTER_SERVICE_URL", "http://explanation-letter-service:8000")

def get_users():
    logger.info("Fetching all underwriters")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, email, role FROM users WHERE role = %s", (role,))
    users = cur.fetchall()
    cur.close()
    conn.close()
    return [UserRead(id=u[0], full_name=u[1], email=u[2], role=u[3]) for u in users]

def get_user_by_id(user_id: str):
    logger.info(f"Fetching underwriter with ID: {user_id}")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, email, role FROM users WHERE id = %s AND role = %s", (user_id, role))
    u = cur.fetchone()
    cur.close()
    conn.close()
    if not u:
        raise Exception("User not found")
    return UserRead(id=u[0], full_name=u[1], email=u[2], role=u[3])

def create_user(user: UserCreate):
    logger.info(f"Creating new underwriter: {user.full_name}, {user.email}")
    import bcrypt
    hashed = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (full_name, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (user.full_name, user.email, hashed, role))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return UserRead(id=new_id, full_name=user.full_name, email=user.email, role=role)

def delete_borrower_application(user_id: str):
    try:
        logger.info(f"Deleting borrower application for user ID: {user_id}")
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM decision_log WHERE borrower_id = %s", (user_id,))
        deleted_count = cur.rowcount
        conn.commit()
        if deleted_count == 0:
            raise Exception("No application found for the given user ID")
        logger.info(f"Deleted {deleted_count} record from decision_log for user ID: {user_id}")

        #for rule_evaluation_log
        cur.execute("DELETE FROM rule_evaluation_log WHERE user_id = %s", (user_id,))
        deleted_count = cur.rowcount
        conn.commit()
        logger.info(f"Deleted {deleted_count} record from rule_evaluation_log for user ID: {user_id}")

        #for fairness_audit_log
        cur.execute("DELETE FROM fairness_audit_log WHERE ml_result_id = (select id FROM ml_prediction_results WHERE user_id = %s)", (user_id,))
        deleted_count = cur.rowcount
        conn.commit()
        logger.info(f"Deleted {deleted_count} record from fairness_audit_log for user ID: {user_id}")   

        #do the same for ml_evaluation_log
        cur.execute("DELETE FROM ml_prediction_results WHERE user_id = %s", (user_id,))
        deleted_count = cur.rowcount
        conn.commit()
        logger.info(f"Deleted {deleted_count} record from ml_evaluation_log for user ID: {user_id}")

        #do the same for documents
        cur.execute("DELETE FROM documents WHERE user_id = %s", (user_id,))
        deleted_count = cur.rowcount
        conn.commit()
        logger.info(f"Deleted {deleted_count} record from ml_evaluation_log for user ID: {user_id}")
        cur.close()
        conn.close()
        return {"message": f"Deleted application for user ID: {user_id}"}
    except Exception as e:
        logger.exception(f"Error deleting borrower application for user ID: {user_id}: {e}")
        return {"error": "Error deleting borrower application"} 
    
def send_ml_model_train_request(underwriter_id: str):
    headers = {
        "x-user-id": underwriter_id
    }

    try:
        with httpx.Client() as client:
            response = client.post(f"{ML_DECISION_SERVICE_URL}/train-ml-model", headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Training failed: {response.text}"
                )
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Internal call failed: {str(e)}")
    
def generate_decision_exp_letter(borrower_id: str, underwriter_id: str):
    logger.info(f"Generating decision explanation letter for borrower ID: {borrower_id} by underwriter ID: {underwriter_id}")
    # Validate borrower role
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT role FROM users WHERE id = %s", (underwriter_id,))
        user = cur.fetchone()
        if not user or user[0] != "underwriter":
            raise HTTPException(status_code=403, detail="This user is not allowed to generate explanation letters")
    except HTTPException as he:
        raise he
    finally:
        cur.close()
        conn.close()
    explanation = explain_borrower_application(borrower_id)
    payload = explanation.model_dump()
    logger.info(f"Explanation fetched for borrower ID {borrower_id}: {payload}")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{EXPLANATION_LETTER_SERVICE_URL}/generate_letter",
                json=payload
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Generate Letter failed: {response.text}"
                )
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Internal call failed: {str(e)}")