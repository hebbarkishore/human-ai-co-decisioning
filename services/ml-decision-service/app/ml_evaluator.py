from db import get_connection
from models import MLRequest, MLResult
from logger import logger
import json
from datetime import datetime
import uuid
import joblib
import shap
import numpy as np
import pandas as pd

model = joblib.load("ml_model.pkl")
explainer = shap.TreeExplainer(model)

def predict_from_parsed_data(parsed_data: dict):
    # Build DataFrame with proper feature names
    features = pd.DataFrame([[
        clean_salary(parsed_data["annual_salary"]),
        parsed_data["credit_score"],
        parsed_data["employment_years"]
    ]], columns=["salary", "credit_score", "employment_years"])

    # Predict probabilities
    prob = model.predict_proba(features)[0]
    decision = "accepted" if prob[1] > 0.5 else "rejected"

    # SHAP values
    shap_output = explainer.shap_values(features)
    if isinstance(shap_output, list):
        shap_values = shap_output[1]  # Class 1 = accepted
    else:
        shap_values = shap_output

    shap_summary = {
        col: float(round(shap_values[0, i].flatten()[0], 4))  
        for i, col in enumerate(features.columns)
    }

    return {
        "predicted_decision": decision,
        "confidence": float(round(prob[1], 2)),
        "shap_summary": shap_summary
    }

def evaluate_ml_decision(request: MLRequest) -> dict:
    logger.info(f"🔍 Evaluating ML decision for user {request.user_id}, document {request.document_id}")
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
        logger.info(f"Fetched parsed data for ML evaluation: {parsed_data}")

        # Step 2: Based on the document which contains name, personal details, salary and many more, Execute ML decision
        ml_result = predict_from_parsed_data(parsed_data)

        prediction_decision = ml_result["predicted_decision"]
        confidence_score = ml_result["confidence"]
        shap_summary = ml_result["shap_summary"]
        
        logger.info(f"ML Prediction: {prediction_decision} with confidence {confidence_score}, SHAP: {shap_summary}")
        # Step 3: Insert into ml_prediciton_result
        ml_result_id = str(uuid.uuid4())
        evaluated_at = datetime.now()

        cur.execute("""
            INSERT INTO ml_prediction_results (id, user_id, document_id, predicted_decision, confidence_score, shap_summary, evaluated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            ml_result_id,
            request.user_id,
            request.document_id,
            prediction_decision,
            confidence_score,
            json.dumps(shap_summary),
            evaluated_at
        ))

        conn.commit()
        logger.info(f"Inserted ML log {ml_result_id}")

        return {
            "status": prediction_decision,
            "confidence": str(confidence_score),
            "ml_result_id": str(ml_result_id)
        }

    except Exception as e:
        logger.error(f"Error in evaluate_ml: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def clean_salary(value: str):
    return float(value.replace("$", "").replace(",", "").strip())

if __name__ == "__main__":
    parsed_data = {'ssn': 'XXX-XX-1234', 'date': '2025-10-28', 'email': 'john.doe@example.com', 'phone': '(123) 456-7890', 'assets': 'Checking Account-$20,000,  Retirement Fund-$85,000,Vehicle-2021 Toyota Camry ($18,000)', 'address': '123 Main Street, XYZ, NY 23456', 'purpose': 'Purchase of Primary Residence', 'employer': 'ABC Corp', 'position': 'Senior Software Engineer', 'loan_term': '30 years', 'liabilities': 'Credit Card Debt-$2,500,Auto Loan-$10,000', 'credit_score': '600', 'annual_salary': '$145,000', 'date_of_birth': '1984-09-12', 'interest_rate': '6.25%', 'applicant_name': 'John Doe', 'employment_years': '10', 'property_address': '', 'applicant_signature': '________________________', 'loan_amount_requested': '$400,000'}

    ml_result = predict_from_parsed_data(parsed_data)
    prediction_decision = ml_result["predicted_decision"]
    confidence_score = ml_result["confidence"]
    shap_summary = ml_result["shap_summary"]
    print("Prediction:", ml_result)