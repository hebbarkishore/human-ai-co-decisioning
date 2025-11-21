from fastapi import HTTPException
from db import get_connection
import bcrypt

def authenticate(email: str, password: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id, full_name, password_hash, role FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user_id, full_name, password_hash, role = user

        if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return {
            "id": user_id,
            "full_name": full_name,
            "email": email,
            "role": role
        }

    finally:
        cur.close()
        conn.close()