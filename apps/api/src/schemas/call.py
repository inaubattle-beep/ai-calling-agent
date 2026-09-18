from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TranscriptMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    call_id: str
    speaker: str
    text: str
    language: str
    latency_ms: Optional[int] = None
    timestamp: datetime


class CallCreate(BaseModel):
    phone_number: str = Field(..., json_schema_extra={"example": "+8801712345678"})
    direction: str = Field(default="OUTBOUND", json_schema_extra={"example": "OUTBOUND"})
    language: str = Field(default="bn-BD", json_schema_extra={"example": "bn-BD"})
    agent_id: str = Field(default="ai-receptionist-01", json_schema_extra={"example": "ai-receptionist-01"})


class CallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    phone_number: str
    direction: str
    language: str
    status: str
    agent_id: Optional[str] = None
    started_at: datetime
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration: int = 0


class CallDetailResponse(CallResponse):
    transcripts: List[TranscriptMessageResponse] = []
