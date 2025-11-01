from fastapi import APIRouter,Header
from models import MLRequest, MLResult
from ml_evaluator import evaluate_ml_decision
from train_ml_model import train_model_from_db

router = APIRouter()

@router.post("/evaluate-ml-decision", response_model=MLResult)
def evaluate(user_input: MLRequest):
    return evaluate_ml_decision(user_input)


@router.post("/train-ml-model")
def train_ml_model(x_user_id: str = Header(...)):
    return train_model_from_db(x_user_id)