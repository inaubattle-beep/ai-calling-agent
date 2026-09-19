from typing import List, Optional
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
    description: str
    greeting: str
    system_prompt: str
    supported_languages: List[str]
    enabled: bool


class AgentCreate(BaseModel):
    id: str
    name: str
    model: str = "mock-receptionist-v1"
    primary_language: str = "bn-BD"
    description: str = "AI voice agent"
    greeting: str = "আসসালামু আলাইকুম, আমি কীভাবে সাহায্য করতে পারি?"
    system_prompt: str = "You are a polite, helpful telephone AI receptionist."
    supported_languages: List[str] = ["bn-BD", "en-US", "mixed"]
    enabled: bool = True


class AgentUpdate(BaseModel):
    name: str
    model: str
    primary_language: str
    description: str
    greeting: str
    system_prompt: str
    supported_languages: List[str]
    enabled: bool
