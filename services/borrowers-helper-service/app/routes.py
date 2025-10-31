from fastapi import UploadFile, File, APIRouter, HTTPException
from models import UserCreate, UserRead
from user_service import get_users, get_user_by_id, create_user, verify_user_eligibility

router = APIRouter(prefix="/borrower-helper-service")

@router.get("/borrowers", response_model=list[UserRead])
def list_users():
    return get_users()

@router.get("/borrower/{user_id}", response_model=UserRead)
def get_user( user_id: str):
    return get_user_by_id(user_id)

@router.post("/borrower", response_model=UserRead)
def add_user(user: UserCreate):
    return create_user(user)

@router.post("/borrower/{user_email}/check-eligibility")
def check_eligibility(user_email: str, file: UploadFile = File(...)):
    return verify_user_eligibility(user_email, file)