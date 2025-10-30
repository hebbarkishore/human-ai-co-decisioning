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
from logger import logger

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


def verify_user_eligibility(email: str, file: UploadFile):
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

    logger.info("Checking eligibility for user_id: %s, document: %s", user_id, document_name)

    # Step 2: Get latest decision
    cur.execute("""
        SELECT final_decision FROM decision_log
        WHERE borrower_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    decision_row = cur.fetchone()
    latest_decision = decision_row[0] if decision_row else None

    logger.info("Latest decision for user_id %s: %s", user_id, latest_decision)

    # Step 3: If approved, exit early
    if latest_decision == "approved":
        cur.close()
        conn.close()
        return {"status": "approved", "message": "Loan already approved."}
    
    logger.info("Proceeding to document submission for user_id %s", user_id)

    # Step 4: Check if document already exists
    cur.execute("""
        SELECT id FROM documents
        WHERE user_id = %s AND document_name = %s AND document_type = %s
    """, (user_id, document_name, document_type))
    doc_exists = cur.fetchone()

    logger.info("Document exists check for user_id %s, latest_decision %s, document %s: %s", user_id, latest_decision, document_name, bool(doc_exists))

    if doc_exists:
        if latest_decision == "rejected":
            cur.close()
            conn.close()
            return {"status": "rejected", "message": "Application rejected. No more documents accepted."}
        return {"status": latest_decision or "unknown", "message": "Document already submitted."}

    if latest_decision and latest_decision != "request_evidence":
        cur.close()
        conn.close()
        return {"status": latest_decision, "message": f"Cannot accept documents. Last decision: {latest_decision}"}

    # Step 5: Read and extract metadata
    contents = file.file.read()
    metadata = extract_metadata_from_file_bytes(file.filename, contents)

    # Step 6: Insert document
    cur.execute("""
        INSERT INTO documents (user_id, document_name, document_content, document_type, parsed_data)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (user_id, document_name, contents, document_type, json.dumps(metadata)))
    doc_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    # Step 7: Notify coordinator
    notify_response = call_decision_coordinator(user_id, doc_id)
    logger.info("decision coordinator for user_id %s, document_id %s, response %s", user_id, doc_id, notify_response)

    return {"message": notify_response, "document_id": doc_id}


def call_decision_coordinator(user_id: str, document_id: str):
    payload = {
        "user_id": user_id,
        "document_id": document_id
    }

    try:
        response = httpx.post(f"{DECISION_COORDINATOR_URL}/process-decision", json=payload)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as exc:
        logger.error(f"❌ Error contacting decision-coordinator-service: {exc}")
        return {"error": "Coordinator not reachable"}