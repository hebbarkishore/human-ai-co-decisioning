from fastapi import APIRouter, HTTPException
from models import ExplanationResponse,ManualDecisionUpdateRequest, UserCreate, UserRead
from explanation_service import explain_borrower_application
from override_decision_service import update_decision_by_underwriter
from underwriter_service import get_users, get_user_by_id, create_user, delete_borrower_application

router = APIRouter(prefix="/underwriter-helper-service")

@router.get("/application-explanation/borrower/{user_id}", response_model=ExplanationResponse)
def explain_usr_application(user_id: str):
    return explain_borrower_application(user_id)

@router.post("/manual-decision-update")
def manual_decision_update(request: ManualDecisionUpdateRequest):
    return update_decision_by_underwriter(request)


@router.get("/underwriters", response_model=list[UserRead])
def list_users():
    return get_users()

@router.get("/underwriter/{user_id}", response_model=UserRead)
def get_user( user_id: str):
    return get_user_by_id(user_id)

@router.post("/underwriter", response_model=UserRead)
def add_user(user: UserCreate):
    return create_user(user)

#router for delete application
@router.delete("/application/borrower/{user_id}")
def delete_application(user_id: str):
    return delete_borrower_application(user_id)