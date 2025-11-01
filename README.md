# Human-AI Co-Decisioning System

A research PoC integrating ML, rule-based engines, fairness auditing, and human overrides in mortgage underwriting.

## 🏦 Project Overview

**Human-AI Co-Decisioning for Mortgage Underwriting** is a modular, microservices-based platform designed to streamline, explain, and improve loan approval decisions through a hybrid **AI + Human** approach.

The system intelligently combines:

-  **Rule-Based Automation** — built on business logic and regulatory rules  
-  **Machine Learning Predictions** — enhanced with SHAP-based explainability  
-  **Fairness & Bias Auditing** — to ensure compliance and ethical transparency  
-  **Manual Underwriter Overrides** — empowering human experts to review and adjust AI outcomes  

It enables underwriters to review, override, and retrain ML-driven decisions with full transparency helping financial institutions comply with regulations such as **ECOA**, **CFPB**, and **GDPR**, while continuously improving decision quality through real-time feedback.

## Problem It Solves
Traditional mortgage underwriting relies heavily on either:

- **Rigid rule engines** — lack flexibility and adaptability to nuanced borrower profiles.  
- **Black-box ML models** — lack transparency and explainability in decision-making.

This project solves both problems by:

-  **Exposing transparent explanations** for AI-driven decisions  
-  **Allowing underwriters to override decisions**  
-  **Tracking fairness and bias metrics** in real time  
-  **Retraining the ML model with human feedback** (via a shadow model loop)

## How to Run (Docker Compose)
docker-compose up --build

## Services Overview
| **Service**          | **Port** | **Swagger URL**                    |
|-----------------------|----------|------------------------------------|
| Borrowers Helper      | 8001     | [http://localhost:8001/docs](http://localhost:8001/docs) |
| Decision Coordinator  | 8002     | [http://localhost:8002/docs](http://localhost:8002/docs) |
| Rule Engine           | 8003     | [http://localhost:8003/docs](http://localhost:8003/docs) |
| ML Decision           | 8004     | [http://localhost:8004/docs](http://localhost:8004/docs) |
| Fairness Auditor      | 8005     | [http://localhost:8005/docs](http://localhost:8005/docs) |
| Underwriter Helper    | 8006     | [http://localhost:8006/docs](http://localhost:8006/docs) |

## 🧪 API Testing with Postman

**Download Postman Collection:**  
[HumanAI_Fintech_Collection.postman_collection.json](HumanAI_Fintech_Collection.postman_collection.json)

### How to Use

1. **Import** the collection into Postman.  
2. You can use the default borrower and underwriter set up during startup, or create new ones using the APIs:  
   - `create-borrower`  
   - `create-underwriter`  
3. Use the `send-application` API to verify borrower eligibility against the Rule Engine and ML Engine.  
   - Input the borrower’s **email** in the request body.  
4. Use the `explain-application-service` API to view decision explanations (for both approved and rejected applications).  
5. As an **underwriter**, update an application’s decision using the `update-decision` API.  
   - This will also create a new **training record**, which is used later for ML re-training.  
6. Trigger model retraining manually using the `request-ml-training` API.  
   - Only **underwriters** are authorized to execute this; include the **underwriter ID** in the request header.  
7. To re-test the workflow, delete existing borrower applications using the `delete-user-applications` API.

---

## 🤖 ML Model Management

- **Old trained models** are backed up to: `trained_model_history/`  
- **New trained model** replaces: `ml_model.pkl`  
- **Retraining** is triggered manually through the `request-ml-training` API  

> Tip: Ensure the training data directory is mounted as a persistent volume if using Docker, so retrained models are not lost after container restarts.

---

## 📜 License

This project is intended for **research and educational purposes only**.  
Please consult with your **legal or compliance team** before deploying in any production environment.
