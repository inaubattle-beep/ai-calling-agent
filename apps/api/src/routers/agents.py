import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.agent import AgentModel
import json

from ..schemas.agent import AgentResponse

router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.get("", response_model=List[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AgentModel))
    agents = res.scalars().all()
    return [
        AgentResponse.model_validate(
            {**agent.__dict__, "supported_languages": json.loads(agent.supported_languages)}
        )
        for agent in agents
    ]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(AgentModel, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse.model_validate(
        {**agent.__dict__, "supported_languages": json.loads(agent.supported_languages)}
    )
