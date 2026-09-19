import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.agent import AgentModel
from ..models.settings import AppSettingsModel
from ..schemas.agent import AgentCreate, AgentResponse, AgentUpdate
from ..schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def settings_response(settings: AppSettingsModel) -> SettingsResponse:
    return SettingsResponse(
        id=settings.id,
        business_name=settings.business_name,
        dashboard_title=settings.dashboard_title,
        sip_extension=settings.sip_extension,
        default_language=settings.default_language,
        supported_languages=json.loads(settings.supported_languages),
        default_phone_number=settings.default_phone_number,
        default_agent_id=settings.default_agent_id,
    )


def agent_response(agent: AgentModel) -> AgentResponse:
    values = {column.name: getattr(agent, column.name) for column in AgentModel.__table__.columns}
    values["supported_languages"] = json.loads(agent.supported_languages)
    return AgentResponse(**values)


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    settings = await db.get(AppSettingsModel, 1)
    if not settings:
        settings = AppSettingsModel(id=1)
        db.add(settings)
        await db.flush()
    return settings_response(settings)


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(payload: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    settings = await db.get(AppSettingsModel, 1)
    if not settings:
        settings = AppSettingsModel(id=1)
        db.add(settings)
    if payload.default_language not in payload.supported_languages:
        raise HTTPException(status_code=422, detail="Default language must be supported")
    for key, value in payload.model_dump().items():
        setattr(settings, key, json.dumps(value) if key == "supported_languages" else value)
    await db.flush()
    return settings_response(settings)


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(payload: AgentCreate, db: AsyncSession = Depends(get_db)):
    if await db.get(AgentModel, payload.id):
        raise HTTPException(status_code=409, detail="Agent already exists")
    agent = AgentModel(
        **payload.model_dump(exclude={"supported_languages"}),
        supported_languages=json.dumps(payload.supported_languages),
    )
    db.add(agent)
    await db.flush()
    return agent_response(agent)


@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, payload: AgentUpdate, db: AsyncSession = Depends(get_db)):
    agent = await db.get(AgentModel, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    for key, value in payload.model_dump().items():
        setattr(agent, key, json.dumps(value) if key == "supported_languages" else value)
    await db.flush()
    return agent_response(agent)