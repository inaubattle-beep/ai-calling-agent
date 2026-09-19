from sqlalchemy import Column, Integer, String, Text

from ..database import Base


class AppSettingsModel(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, default=1)
    business_name = Column(String(160), nullable=False, default="Bilingual AI Contact Center")
    dashboard_title = Column(String(160), nullable=False, default="Bilingual AI Contact Center")
    sip_extension = Column(String(32), nullable=False, default="7000")
    default_language = Column(String(16), nullable=False, default="bn-BD")
    supported_languages = Column(Text, nullable=False, default='["bn-BD", "en-US", "mixed"]')
    default_phone_number = Column(String(32), nullable=False, default="+8801819203040")
    default_agent_id = Column(String(64), nullable=False, default="ai-receptionist-01")