from fastapi import APIRouter
from models import MLRequest, MLResult
from ml_evaluator import evaluate_ml_decision

router = APIRouter()

@router.post("/evaluate-ml-decision", response_model=MLResult)
def evaluate(user_input: MLRequest):
    return evaluate_ml_decision(user_input)