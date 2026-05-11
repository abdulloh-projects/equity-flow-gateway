from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(
        None, description="Session ID for conversation continuity"
    )


class ChatResponse(BaseModel):
    response: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session ID (new or existing)")
    sources: List[str] = Field(
        default_factory=list, description="Knowledge-base files used"
    )


class InitResponse(BaseModel):
    message: str
    chunks_indexed: int


class HealthResponse(BaseModel):
    status: str
    detail: Optional[str] = None
