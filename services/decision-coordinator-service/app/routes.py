from fastapi import APIRouter
from models import DecisionRequest
from services.decision_service import handle_decision_request

router = APIRouter()

@router.post("/process-decision")
def process_decision(request: DecisionRequest):
    return handle_decision_request(request.user_id, request.document_id)