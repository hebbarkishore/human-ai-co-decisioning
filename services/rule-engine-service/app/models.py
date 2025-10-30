from pydantic import BaseModel
from typing import Dict, Optional

class RuleRequest(BaseModel):
    user_id: str
    document_id: str

class RuleResult(BaseModel):
    status: str  # "pass" or "fail"
    reasons: Dict[str, str]  # {"rule_name": "Passed/Failed: Reason"}
    rule_result_id: Optional[str] = None