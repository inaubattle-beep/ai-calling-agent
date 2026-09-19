import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.src.database import init_db
from apps.api.src.main import app
from apps.api.src.services.call_manager import call_manager


@pytest.mark.asyncio
async def test_admin_can_customize_platform_and_agent_data():
    await init_db()
    await call_manager.init_agent_record()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        settings_response = await client.get("/api/admin/settings")
        assert settings_response.status_code == 200
        settings = settings_response.json()
        original_settings = dict(settings)
        settings["dashboard_title"] = "Operations Console"
        updated_settings = await client.put("/api/admin/settings", json=settings)
        assert updated_settings.status_code == 200
        assert updated_settings.json()["dashboard_title"] == "Operations Console"

        agent = (await client.get("/api/agents")).json()[0]
        original_agent = dict(agent)
        agent["name"] = "Configured Receptionist"
        editable = {
            key: agent[key]
            for key in (
                "name",
                "model",
                "primary_language",
                "description",
                "greeting",
                "system_prompt",
                "supported_languages",
                "enabled",
            )
        }
        updated_agent = await client.put(f"/api/admin/agents/{agent['id']}", json=editable)
        assert updated_agent.status_code == 200
        assert updated_agent.json()["name"] == "Configured Receptionist"

        await client.put("/api/admin/settings", json=original_settings)
        await client.put(
            f"/api/admin/agents/{agent['id']}",
            json={key: original_agent[key] for key in editable},
        )