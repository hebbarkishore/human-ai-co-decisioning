from fastapi import APIRouter
import asyncio
from models import DecisionRequest
from services.decision_service import handle_decision_request
from logger import logger

router = APIRouter()

@router.post("/process-decision")
def process_decision(request: DecisionRequest):
    # Launch entire handling pipeline as a background task
    return handle_decision_request(request.user_id, request.document_id)