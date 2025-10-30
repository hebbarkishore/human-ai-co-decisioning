from fastapi import APIRouter, HTTPException
from models import FARequest, FAResult
from fairness_evaluator import evaluate_fairness

router = APIRouter()

@router.post("/fairness-auditor", response_model=FAResult)
def evaluate(user_input: FARequest):
    return evaluate_fairness(user_input)