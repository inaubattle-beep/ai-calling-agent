from typing import List
from fastapi import APIRouter, Query
from ..events.bus import event_bus
from ..schemas.event import SystemEvent

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.get("", response_model=List[SystemEvent])
async def list_events(limit: int = Query(50, le=100)):
    return event_bus.get_recent_events(limit=limit)
