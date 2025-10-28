from pydantic import BaseModel

class DecisionRequest(BaseModel):
    user_id: str
    document_id: str