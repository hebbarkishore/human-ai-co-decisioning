# Human-AI Co-Decisioning System

A research PoC integrating ML, rule-based engines, fairness auditing, and human overrides in mortgage underwriting.

## Project Overview

Human-AI Co-Decisioning for Mortgage Underwriting is a modular microservices-based platform designed to streamline, explain, and improve loan approval decisions through a hybrid AI + Human approach.
The system intelligently combines:
    Rule-Based Automation (via business logic and regulatory rules),
    Machine Learning Predictions (with SHAP-based explainability),
    Fairness & Bias Auditing,
    Manual Underwriter Overrides.
It empowers underwriters to review, override, and retrain ML decisions with full transparency, helping financial institutions comply with fairness regulations (e.g., ECOA, CFPB, GDPR) and adapt to real-time feedback.

## Problem It Solves
Traditional mortgage underwriting relies heavily on either:
	•	rigid rule engines (lacking flexibility), or
	•	black-box ML models (lacking explainability).

This project solves both problems by:
	•	Exposing transparent explanations for AI-driven decisions
	•	Allowing underwriters to override decision
    •	Tracking fairness and bias metrics in real time
	•	Retraining the ML model with human feedback (shadow model loop)

## How to Run (Docker Compose)
docker-compose up --build

## Services Overview
Services             |     Port  |  Swagger URL
-----------------------------------------------
Borrowers Helper     |    8001   | http://localhost:8001/docs
Decision Coordinator |    8002   | http://localhost:8002/docs
Rule Engine          |    8003   | http://localhost:8003/docs
ML Decision          |    8004   | http://localhost:8004/docs
Fairness Auditor     |    8005   | http://localhost:8005/docs
Underwriter Helper   |    8006   | http://localhost:8006/docs

## API Testing with Postman
Download Postman collection: HumanAI_Fintech_Collection.postman_collection.json
How to Use:
	1.	Import collection into Postman
	2.	You can use the default borrower and underwriter which was setup during the startup or you can create new using the APIs create-borrower and create-underwriter apis
    3.  Then use the send-application API, this will verify if the borrower is eligible for the loan by checking against rules engine and ML engine. (you need to input the borrower email)
    4.  You can use explain-application-service for the approval and rejected decision details.
    5.  As a underwriter, you can update the decision of an application using update-decision, this will also create the new training record which later can be used for ML re-training.
    6.  request-ml-training API to train the ML based on the training data(only underwriter has a permission to execute this, please use underwriter id while sending this API under header)
    7.  If you want to retest, then you can delete the previous application using delete-user-applications.

## ML Model Management
   Old trained models are backed up to: trained_model_history/
   New trained model replaces: ml_model.pkl
   Retraining is triggered manually via request-ml-training API

## License
   This project is intended for research and educational use. Please consult with legal or compliance teams before using in production.