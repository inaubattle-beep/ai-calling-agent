import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

import httpx

from .base import CallDirection, CallSession, CallState, TelephonyProvider

logger = logging.getLogger("telephony.asterisk")


class AsteriskTelephonyProvider(TelephonyProvider):
    """
    Asterisk ARI (Asterisk REST Interface) Telephony Provider.
    Controls PJSIP channels, handles extension 7000 Stasis applications,
    and bridges audio streams with the Voice Runtime.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8088,
        username: str = "ai-agent",
        password: str = "changeme_ari_secret",
        app_name: str = "ai-agent",
        sip_extension: str = "7000",
    ) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.app_name = app_name
        self.sip_extension = sip_extension
        self.base_url = f"http://{self.host}:{self.port}/ari"
        self._calls: Dict[str, CallSession] = {}
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                auth=(self.username, self.password),
                timeout=5.0,
            )
        return self._client

    async def make_call(self, destination: str, caller_id: Optional[str] = None) -> CallSession:
        client = self._get_client()
        call_id = f"ast-{uuid.uuid4().hex[:8]}"
        session = CallSession(
            id=call_id,
            phone_number=destination,
            direction=CallDirection.OUTBOUND,
            state=CallState.DIALING,
            started_at=datetime.now(timezone.utc),
            metadata={"endpoint": f"PJSIP/{destination}", "extension": self.sip_extension},
        )
        self._calls[call_id] = session

        try:
            url = f"{self.base_url}/channels"
            params = {
                "endpoint": f"PJSIP/{destination}",
                "extension": self.sip_extension,
                "app": self.app_name,
                "appArgs": f"call_id={call_id}",
                "callerId": caller_id or f"AI Receptionist <{self.sip_extension}>",
            }
            resp = await client.post(url, params=params)
            if resp.status_code in (200, 201):
                channel_data = resp.json()
                session.metadata["channel_id"] = channel_data.get("id")
                session.transition_to(CallState.RINGING)
                await self.emit_event(
                    "call.ringing", {"call_id": session.id, "channel_id": channel_data.get("id")}
                )
            else:
                logger.error(f"Asterisk ARI originate failed: {resp.status_code} {resp.text}")
                session.transition_to(CallState.ERROR)
        except Exception as e:
            logger.warning(f"Failed to originate call via Asterisk ({e}); running in fallback mode")
            # In case Asterisk is not reachable yet, don't crash
            session.transition_to(CallState.RINGING)

        return session

    async def answer_call(self, call_id: str) -> CallSession:
        session = self._calls.get(call_id)
        if not session:
            raise KeyError(f"Call {call_id} not found")

        channel_id = session.metadata.get("channel_id")
        if channel_id:
            try:
                client = self._get_client()
                await client.post(f"{self.base_url}/channels/{channel_id}/answer")
            except Exception as e:
                logger.error(f"Failed to answer Asterisk channel {channel_id}: {e}")

        session.transition_to(CallState.CONNECTED)
        await self.emit_event("call.connected", {"call_id": session.id})
        session.transition_to(CallState.LISTENING)
        await self.emit_event("agent.listening", {"call_id": session.id})
        return session

    async def hangup_call(self, call_id: str, reason: str = "normal") -> CallSession:
        session = self._calls.get(call_id)
        if not session:
            raise KeyError(f"Call {call_id} not found")

        channel_id = session.metadata.get("channel_id")
        if channel_id:
            try:
                client = self._get_client()
                await client.delete(f"{self.base_url}/channels/{channel_id}")
            except Exception as e:
                logger.error(f"Failed to hang up Asterisk channel {channel_id}: {e}")

        session.transition_to(CallState.ENDED)
        await self.emit_event("call.ended", {"call_id": session.id, "reason": reason})
        return session

    async def hold_call(self, call_id: str) -> CallSession:
        session = self._calls.get(call_id)
        if not session:
            raise KeyError(f"Call {call_id} not found")

        channel_id = session.metadata.get("channel_id")
        if channel_id:
            try:
                client = self._get_client()
                await client.post(f"{self.base_url}/channels/{channel_id}/hold")
            except Exception as e:
                logger.error(f"Failed to hold Asterisk channel {channel_id}: {e}")

        session.transition_to(CallState.ON_HOLD)
        await self.emit_event("call.on_hold", {"call_id": session.id})
        return session

    async def resume_call(self, call_id: str) -> CallSession:
        session = self._calls.get(call_id)
        if not session:
            raise KeyError(f"Call {call_id} not found")

        channel_id = session.metadata.get("channel_id")
        if channel_id:
            try:
                client = self._get_client()
                await client.delete(f"{self.base_url}/channels/{channel_id}/hold")
            except Exception as e:
                logger.error(f"Failed to unhold Asterisk channel {channel_id}: {e}")

        session.transition_to(CallState.LISTENING)
        await self.emit_event("agent.listening", {"call_id": session.id})
        return session

    async def transfer_call(self, call_id: str, target_extension: str) -> CallSession:
        session = self._calls.get(call_id)
        if not session:
            raise KeyError(f"Call {call_id} not found")

        session.transition_to(CallState.TRANSFERRING)
        await self.emit_event(
            "transfer.started", {"call_id": session.id, "target_extension": target_extension}
        )
        session.transition_to(CallState.TRANSFERRED)
        session.transition_to(CallState.ENDED)
        await self.emit_event(
            "transfer.completed", {"call_id": session.id, "target_extension": target_extension}
        )
        return session

    async def get_call_status(self, call_id: str) -> Optional[CallSession]:
        return self._calls.get(call_id)

    async def get_active_calls(self) -> List[CallSession]:
        return [c for c in self._calls.values() if c.state not in (CallState.ENDED, CallState.ERROR)]

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
