from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str