from typing import Optional
from pydantic import BaseModel, ConfigDict


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: str
    current_call_id: Optional[str] = None
    model: str
    primary_language: str
    stt_latency_ms: int
    llm_latency_ms: int
    tts_latency_ms: int
