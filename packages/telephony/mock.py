import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from .base import CallDirection, CallSession, CallState, TelephonyProvider

logger = logging.getLogger("telephony.mock")


class MockTelephonyProvider(TelephonyProvider):
    """
    Mock Telephony Provider for local development, tests, and CI/CD.
    Simulates complete call lifecycles without requiring Asterisk or a physical PBX trunk.
    """

    def __init__(self) -> None:
        super().__init__()
        self._calls: Dict[str, CallSession] = {}
        self._background_tasks: set[asyncio.Task] = set()

    async def make_call(
        self, destination: str, caller_id: Optional[str] = None, call_id: Optional[str] = None
    ) -> CallSession:
        cid = call_id or f"mock-{uuid.uuid4().hex[:8]}"
        session = CallSession(
            id=cid,
            phone_number=destination,
            direction=CallDirection.OUTBOUND,
            state=CallState.DIALING,
            started_at=datetime.now(timezone.utc),
            metadata={"caller_id": caller_id or "+8801700000000", "mock": True},
        )
        self._calls[cid] = session

        await self.emit_event(
            "call.created",
            {"call_id": session.id, "phone_number": destination, "direction": session.direction.value},
        )

        # Auto-advance to RINGING then CONNECTED for mock convenience
        task = asyncio.create_task(self._simulate_outbound_lifecycle(session))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        return session

    async def simulate_inbound_call(
        self,
        phone_number: str = "+8801819203040",
        language: str = "bn-BD",
        call_id: Optional[str] = None,
    ) -> CallSession:
        cid = call_id or f"mock-in-{uuid.uuid4().hex[:8]}"
        session = CallSession(
            id=cid,
            phone_number=phone_number,
            direction=CallDirection.INBOUND,
            state=CallState.RINGING,
            language=language,
            started_at=datetime.now(timezone.utc),
            metadata={"mock": True, "extension": "7000"},
        )
        self._calls[cid] = session

        await self.emit_event(
            "call.created",
            {"call_id": session.id, "phone_number": phone_number, "direction": session.direction.value},
        )
        await self.emit_event("call.ringing", {"call_id": session.id, "state": session.state.value})

        return session

    async def _simulate_outbound_lifecycle(self, session: CallSession) -> None:
        await asyncio.sleep(0.5)
        if session.id in self._calls and session.state == CallState.DIALING:
            session.transition_to(CallState.RINGING)
            await self.emit_event("call.ringing", {"call_id": session.id, "state": session.state.value})
            await asyncio.sleep(1.0)
            if session.id in self._calls and session.state == CallState.RINGING:
                session.transition_to(CallState.CONNECTED)
                await self.emit_event("call.connected", {"call_id": session.id, "state": session.state.value})
                session.transition_to(CallState.LISTENING)
                await self.emit_event("agent.listening", {"call_id": session.id, "state": session.state.value})

    async def answer_call(self, call_id: str) -> CallSession:
        session = self._calls.get(call_id)
        if not session:
            session = CallSession(id=call_id, state=CallState.RINGING)
            self._calls[call_id] = session

        if session.state == CallState.DIALING:
            session.transition_to(CallState.RINGING)

        if session.state in (CallState.RINGING, CallState.IDLE):
            session.transition_to(CallState.CONNECTED)
            await self.emit_event("call.connected", {"call_id": session.id, "state": session.state.value})
            session.transition_to(CallState.LISTENING)
            await self.emit_event("agent.listening", {"call_id": session.id, "state": session.state.value})
        elif session.state == CallState.CONNECTED:
            session.transition_to(CallState.LISTENING)
            await self.emit_event("agent.listening", {"call_id": session.id, "state": session.state.value})

        return session

    async def hangup_call(self, call_id: str, reason: str = "normal") -> CallSession:
        session = self._calls.get(call_id)
        if not session:
            session = CallSession(id=call_id, state=CallState.ENDED)
            self._calls[call_id] = session
            return session

        if session.state != CallState.ENDED:
            session.transition_to(CallState.ENDED)
            session.metadata["hangup_reason"] = reason
            await self.emit_event(
                "call.ended",
                {
                    "call_id": session.id,
                    "state": session.state.value,
                    "duration": session.duration,
                    "reason": reason,
                },
            )

        return session

    async def hold_call(self, call_id: str) -> CallSession:
        session = self._calls.get(call_id)
        if not session:
            raise KeyError(f"Call {call_id} not found")

        session.transition_to(CallState.ON_HOLD)
        await self.emit_event("call.on_hold", {"call_id": session.id, "state": session.state.value})
        return session

    async def resume_call(self, call_id: str) -> CallSession:
        session = self._calls.get(call_id)
        if not session:
            raise KeyError(f"Call {call_id} not found")

        session.transition_to(CallState.LISTENING)
        await self.emit_event("agent.listening", {"call_id": session.id, "state": session.state.value})
        return session

    async def transfer_call(self, call_id: str, target_extension: str) -> CallSession:
        session = self._calls.get(call_id)
        if not session:
            raise KeyError(f"Call {call_id} not found")

        session.transition_to(CallState.TRANSFERRING)
        await self.emit_event(
            "transfer.started",
            {"call_id": session.id, "target_extension": target_extension, "state": session.state.value},
        )
        # Simulate transfer completion
        session.transition_to(CallState.TRANSFERRED)
        session.transition_to(CallState.ENDED)
        await self.emit_event(
            "transfer.completed",
            {"call_id": session.id, "target_extension": target_extension, "state": session.state.value},
        )
        return session

    async def update_state(self, call_id: str, new_state: CallState) -> CallSession:
        session = self._calls.get(call_id)
        if not session:
            raise KeyError(f"Call {call_id} not found")

        session.transition_to(new_state)
        event_name = f"call.state_changed"
        if new_state == CallState.LISTENING:
            event_name = "agent.listening"
        elif new_state == CallState.THINKING:
            event_name = "agent.thinking"
        elif new_state == CallState.SPEAKING:
            event_name = "agent.speaking"

        await self.emit_event(
            event_name,
            {"call_id": session.id, "state": session.state.value, "language": session.language},
        )
        return session

    async def get_call_status(self, call_id: str) -> Optional[CallSession]:
        return self._calls.get(call_id)

    async def get_active_calls(self) -> List[CallSession]:
        return [c for c in self._calls.values() if c.state not in (CallState.ENDED, CallState.ERROR)]
