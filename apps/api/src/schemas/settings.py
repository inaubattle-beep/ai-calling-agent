from typing import List

from pydantic import BaseModel, ConfigDict, Field


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_name: str
    dashboard_title: str
    sip_extension: str
    default_language: str
    supported_languages: List[str]
    default_phone_number: str
    default_agent_id: str


class SettingsUpdate(BaseModel):
    business_name: str = Field(min_length=1, max_length=160)
    dashboard_title: str = Field(min_length=1, max_length=160)
    sip_extension: str = Field(min_length=1, max_length=32)
    default_language: str = Field(min_length=2, max_length=16)
    supported_languages: List[str] = Field(min_length=1)
    default_phone_number: str = Field(min_length=3, max_length=32)
    default_agent_id: str = Field(min_length=1, max_length=64)