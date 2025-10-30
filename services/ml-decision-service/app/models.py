from pydantic import BaseModel
from typing import Dict, Optional

class MLRequest(BaseModel):
    user_id: str
    document_id: str

class MLResult(BaseModel):
    status: str  # "accepted" or "rejected"
    confidence: Optional[str] = None  
    ml_result_id: Optional[str] = None