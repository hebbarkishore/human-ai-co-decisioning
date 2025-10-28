from fastapi import UploadFile, File, APIRouter, HTTPException
from services.user_service import save_user_document
from models import UserCreate, UserRead
from services.user_service import get_users_by_role, get_user_by_id, create_user, save_user_document

router = APIRouter()

@router.get("/{role}/users", response_model=list[UserRead])
def list_users(role: str):
    return get_users_by_role(role)

@router.get("/{role}/users/{user_id}", response_model=UserRead)
def get_user(role: str, user_id: str):
    return get_user_by_id(user_id, role)

@router.post("/{role}/users", response_model=UserRead)
def add_user(role: str, user: UserCreate):
    return create_user(user, role)

@router.post("/borrower/{user_email}/upload-docs")
async def upload_document(user_email: str, file: UploadFile = File(...)):
    return await save_user_document(user_email, file)