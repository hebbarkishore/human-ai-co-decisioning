from db import get_connection
from models import UserCreate, UserRead
import uuid
from tempfile import NamedTemporaryFile
from fastapi import UploadFile, HTTPException
import os
import json
import re
import io
from docx import Document as DocxDocument
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import httpx

DECISION_COORDINATOR_URL = os.getenv("DECISION_COORDINATOR_URL", "http://decision-coordinator-service:8000")

def get_users_by_role(role: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, email, role FROM users WHERE role = %s", (role,))
    users = cur.fetchall()
    cur.close()
    conn.close()
    return [UserRead(id=u[0], full_name=u[1], email=u[2], role=u[3]) for u in users]

def get_user_by_id(user_id: str, role: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, email, role FROM users WHERE id = %s AND role = %s", (user_id, role))
    u = cur.fetchone()
    cur.close()
    conn.close()
    if not u:
        raise Exception("User not found")
    return UserRead(id=u[0], full_name=u[1], email=u[2], role=u[3])

def create_user(user: UserCreate, role: str):
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

def extract_metadata_from_file_bytes(filename: str, file_bytes: bytes) -> dict:
    ext = os.path.splitext(filename)[1].lower()
    text = ""

    try:
        if ext == ".pdf":
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text()
            doc.close()

        elif ext in [".docx"]:
            docx_stream = io.BytesIO(file_bytes)
            doc = DocxDocument(docx_stream)
            text = "\n".join([para.text for para in doc.paragraphs])

        elif ext in [".jpg", ".jpeg", ".png"]:
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)

        else:
            return {"error": f"Unsupported file type: {ext}"}
    except Exception as e:
        return {"error": f"Failed to extract text: {str(e)}"}

    # Extract key: value pairs
    metadata = {}
    for line in text.splitlines():
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip().lower().replace(" ", "_")
            value = parts[1].strip()
            metadata[key] = value

    return metadata or {"note": "No metadata extracted"}

# ⬇️ Main method
async def save_user_document(email: str, file: UploadFile):
    document_name = os.path.splitext(file.filename)[0]
    document_type = os.path.splitext(file.filename)[1][1:]

    conn = get_connection()
    cur = conn.cursor()

    # Step 1: Get user ID
    cur.execute("SELECT id FROM users WHERE email = %s AND role = 'borrower'", (email,))
    user_row = cur.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="Borrower with provided email not found.")
    user_id = user_row[0]

    # Step 2: Read file and extract metadata
    contents = await file.read()
    metadata = extract_metadata_from_file_bytes(file.filename, contents)

    # Step 3: Save to DB
    cur.execute("""
        INSERT INTO documents (user_id, document_name, document_content, document_type, parsed_data)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (user_id, document_name, contents, document_type, json.dumps(metadata)))
    
    doc_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    # Step 4: Notify decision-coordinator-service
    notify_response = await notify_decision_coordinator(user_id, doc_id)

    return {"message": "Document uploaded successfully", "document_id": doc_id}


async def notify_decision_coordinator(user_id: str, document_id: str):
    payload = {
        "user_id": user_id,
        "document_id": document_id
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{DECISION_COORDINATOR_URL}/process-decision", json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as exc:
        print(f"❌ Error contacting decision-coordinator-service: {exc}")
        return {"error": "Coordinator not reachable"}