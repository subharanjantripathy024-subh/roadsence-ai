from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.models.evidence import Evidence
from app.models.domain import DamageInstance

class AgentRequest(BaseModel):
    question: str
    session_id: str = "default"

class AgentResponse(BaseModel):
    answer: str
    intent: str
    confidence: float
    evidence: List[Dict[str, Any]]
    data: Any

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail
