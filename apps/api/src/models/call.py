from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class CallModel(Base):
    __tablename__ = "calls"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(32), nullable=False)
    direction = Column(String(16), nullable=False, default="INBOUND")  # INBOUND, OUTBOUND
    language = Column(String(16), nullable=False, default="bn-BD")     # bn-BD, en-US, mixed
    status = Column(String(32), nullable=False, default="RINGING")     # CONNECTED, LISTENING, etc.
    agent_id = Column(String(64), nullable=True, default="ai-receptionist-01")
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    answered_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=False, default=0)

    transcripts = relationship("TranscriptMessageModel", back_populates="call", cascade="all, delete-orphan")
