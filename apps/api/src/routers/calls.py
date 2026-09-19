from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.settings import AppSettingsModel
from ..models.call import CallModel
from ..models.transcript import TranscriptMessageModel
from ..schemas.call import CallCreate, CallDetailResponse, CallResponse, TranscriptMessageResponse
from ..services.call_manager import call_manager

router = APIRouter(prefix="/api/calls", tags=["Calls"])


class SimulateRequest(BaseModel):
    phone_number: Optional[str] = None
    language: Optional[str] = None
    barge_in: bool = False


@router.get("", response_model=List[CallResponse])
async def list_calls(
    status: Optional[str] = Query(None, description="Filter by status, e.g. ACTIVE or ENDED"),
    direction: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CallModel).order_by(desc(CallModel.started_at)).limit(limit)

    if status:
        if status.upper() == "ACTIVE":
            stmt = stmt.where(CallModel.status != "ENDED")
        else:
            stmt = stmt.where(CallModel.status == status.upper())

    if direction:
        stmt = stmt.where(CallModel.direction == direction.upper())

    if language:
        stmt = stmt.where(CallModel.language == language)

    res = await db.execute(stmt)
    calls = res.scalars().all()
    return calls


@router.get("/{call_id}", response_model=CallDetailResponse)
async def get_call_detail(call_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(CallModel)
        .where(CallModel.id == call_id)
        .options(selectinload(CallModel.transcripts))
    )
    res = await db.execute(stmt)
    call = res.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # Order transcripts chronologically
    call.transcripts.sort(key=lambda t: t.timestamp)
    return call


@router.post("", response_model=CallResponse, status_code=201)
async def create_call(req: CallCreate):
    try:
        call = await call_manager.create_call(
            phone_number=req.phone_number,
            direction=req.direction,
            language=req.language,
            agent_id=req.agent_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return call


@router.post("/{call_id}/answer")
async def answer_call(call_id: str):
    await call_manager.answer_call(call_id)
    return {"status": "ok", "call_id": call_id}


@router.post("/{call_id}/hangup")
async def hangup_call(call_id: str):
    await call_manager.hangup_call(call_id, reason="operator_terminated")
    return {"status": "ok", "call_id": call_id}


@router.post("/{call_id}/interrupt")
async def interrupt_call(call_id: str):
    """Triggers caller barge-in / speech interruption on active call."""
    await call_manager.trigger_barge_in(call_id)
    return {"status": "ok", "call_id": call_id, "barge_in": True}


@router.post("/simulate")
async def simulate_call(req: SimulateRequest, db: AsyncSession = Depends(get_db)):
    """Starts an automated real-time simulated call with bilingual dialogue."""
    app_settings = await db.get(AppSettingsModel, 1)
    call_id = await call_manager.simulate_realistic_call(
        phone_number=req.phone_number or (app_settings.default_phone_number if app_settings else None),
        language=req.language or (app_settings.default_language if app_settings else None),
        barge_in=req.barge_in,
    )
    return {"status": "simulated", "call_id": call_id}
