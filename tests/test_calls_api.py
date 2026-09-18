import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.src.database import init_db
from apps.api.src.main import app
from apps.api.src.services.call_manager import call_manager


@pytest.mark.asyncio
async def test_calls_crud_and_simulation():
    await init_db()
    await call_manager.init_agent_record()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Outbound Call
        resp = await client.post(
            "/api/calls",
            json={"phone_number": "+8801999887766", "direction": "OUTBOUND", "language": "bn-BD"},
        )
        assert resp.status_code == 201
        call_data = resp.json()
        call_id = call_data["id"]
        assert call_data["phone_number"] == "+8801999887766"

        # 2. Get Call Detail
        detail_resp = await client.get(f"/api/calls/{call_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["id"] == call_id

        # 3. Answer Call
        ans_resp = await client.post(f"/api/calls/{call_id}/answer")
        assert ans_resp.status_code == 200

        # 4. Trigger Interrupt (Barge-in)
        intr_resp = await client.post(f"/api/calls/{call_id}/interrupt")
        assert intr_resp.status_code == 200

        # 5. Hangup Call
        hang_resp = await client.post(f"/api/calls/{call_id}/hangup")
        assert hang_resp.status_code == 200

        # 6. Verify Status is ENDED
        ended_resp = await client.get(f"/api/calls/{call_id}")
        assert ended_resp.json()["status"] == "ENDED"

        # 7. Test Agents endpoint
        agents_resp = await client.get("/api/agents")
        assert agents_resp.status_code == 200
        assert len(agents_resp.json()) >= 1
