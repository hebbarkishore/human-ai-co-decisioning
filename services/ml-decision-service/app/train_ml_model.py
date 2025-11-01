from db import get_connection
from logger import logger
from datetime import datetime
from fastapi import HTTPException
import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

MODEL_FILE = "ml_model.pkl"
MODEL_BACKUP_DIR = "trained_model_history"  

def train_model_from_db(borrower_id: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Validate borrower role
        cur.execute("SELECT role FROM users WHERE id = %s", (borrower_id,))
        user = cur.fetchone()
        if not user or user[0] != "underwriter":
            raise HTTPException(status_code=403, detail="This user is not allowed to train the ML model")

        # Fetch training data
        cur.execute("SELECT salary, credit_score, employment_years, loan_amount, target FROM training_data")
        rows = cur.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No training data found.")

        df = pd.DataFrame(rows, columns=["salary", "credit_score", "employment_years", "loan_amount", "target"])

        X = df[["salary", "credit_score", "employment_years", "loan_amount"]]
        y = df["target"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        # Backup old model if it exists
        if os.path.exists(MODEL_FILE):
            os.makedirs(MODEL_BACKUP_DIR, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(MODEL_BACKUP_DIR, f"ml_model_bkp_{timestamp}.pkl")
            os.rename(MODEL_FILE, backup_path)
            logger.info(f" Old model backed up to {backup_path}")

        # Save new model
        joblib.dump(clf, MODEL_FILE)
        logger.info("New model trained and saved as ml_model.pkl")

        return {
            "message": "Model trained and saved",
            "accuracy": round(accuracy, 4),
            "features": X.columns.tolist()
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f" Error training model: {e}")
        raise HTTPException(status_code=500, detail="Error during model training")
    finally:
        cur.close()
        conn.close()