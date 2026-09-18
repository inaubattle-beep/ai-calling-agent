from sqlalchemy import Column, Integer, String
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
