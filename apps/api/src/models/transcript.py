from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class TranscriptMessageModel(Base):
    __tablename__ = "transcript_messages"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String(64), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    speaker = Column(String(16), nullable=False)  # customer, ai, system
    text = Column(Text, nullable=False)
    language = Column(String(16), nullable=False, default="bn-BD")
    latency_ms = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    call = relationship("CallModel", back_populates="transcripts")
