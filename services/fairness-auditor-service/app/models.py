from pydantic import BaseModel
from typing import Dict, Optional

class FARequest(BaseModel):
    user_id: str
    ml_result_id: str

class FAResult(BaseModel):
    is_biased: bool  
    flagged_features: Dict[str, str]  
    audit_notes: Optional[str] = None
    audit_result_id: Optional[str] = None