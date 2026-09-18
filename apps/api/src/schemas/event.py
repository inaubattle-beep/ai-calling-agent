from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import uuid


class SystemEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event: str
    call_id: Optional[str] = None
    agent_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
