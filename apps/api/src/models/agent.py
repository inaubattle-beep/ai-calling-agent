from sqlalchemy import Boolean, Column, Integer, String, Text
from ..database import Base


class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False, default="ONLINE")  # ONLINE, BUSY, OFFLINE
    current_call_id = Column(String(64), nullable=True)
    model = Column(String(64), nullable=False, default="mock-receptionist-v1")
    primary_language = Column(String(16), nullable=False, default="bn-BD")
    stt_latency_ms = Column(Integer, nullable=False, default=140)
    llm_latency_ms = Column(Integer, nullable=False, default=220)
    tts_latency_ms = Column(Integer, nullable=False, default=180)
    description = Column(Text, nullable=False, default="AI voice agent")
    greeting = Column(Text, nullable=False, default="আসসালামু আলাইকুম, আমি কীভাবে সাহায্য করতে পারি?")
    system_prompt = Column(Text, nullable=False, default="You are a polite, helpful telephone AI receptionist.")
    supported_languages = Column(Text, nullable=False, default='["bn-BD", "en-US", "mixed"]')
    enabled = Column(Boolean, nullable=False, default=True)
