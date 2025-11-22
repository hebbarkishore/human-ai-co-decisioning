from pydantic import BaseModel, EmailStr
from typing import Dict, Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class ExplanationWithCases(BaseModel):
    passed_cases: Optional[str] = None
    failed_cases: Optional[str] = None
    result: Optional[str] = None

class ExplanationDetails(BaseModel):
    rule_explanation: ExplanationWithCases
    ml_explanation: ExplanationWithCases
    fairness_explanation: str

class ExplanationResponse(BaseModel):
    status: str  # approved / rejected / pending
    explanation: ExplanationDetails


class ManualDecisionUpdateRequest(BaseModel):
    underwriter_id: str
    borrower_id: str
    new_status: str  # approved / rejected / pending

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str