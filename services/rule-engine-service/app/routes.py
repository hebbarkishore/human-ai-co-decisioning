from fastapi import APIRouter, HTTPException
from models import RuleRequest, RuleResult
from rule_evaluator import evaluate_rules

router = APIRouter()

@router.post("/evaluate-rules", response_model=RuleResult)
def evaluate(user_input: RuleRequest):
    return evaluate_rules(user_input)