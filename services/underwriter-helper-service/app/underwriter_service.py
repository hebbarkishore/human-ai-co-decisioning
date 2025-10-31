from db import get_connection
from models import UserCreate, UserRead
from logger import logger

role = "underwriter"

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