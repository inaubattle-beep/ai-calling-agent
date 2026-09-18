from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional
import uuid


class CallState(str, Enum):
    IDLE = "IDLE"
    DIALING = "DIALING"
    RINGING = "RINGING"
    CONNECTED = "CONNECTED"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    ON_HOLD = "ON_HOLD"
    TRANSFERRING = "TRANSFERRING"
    TRANSFERRED = "TRANSFERRED"
    ENDED = "ENDED"
    ERROR = "ERROR"


class CallDirection(str, Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


VALID_TRANSITIONS: Dict[CallState, List[CallState]] = {
    CallState.IDLE: [CallState.DIALING, CallState.RINGING, CallState.ERROR],
    CallState.DIALING: [CallState.RINGING, CallState.ENDED, CallState.ERROR],
    CallState.RINGING: [CallState.CONNECTED, CallState.ENDED, CallState.ERROR],
    CallState.CONNECTED: [CallState.LISTENING, CallState.SPEAKING, CallState.ON_HOLD, CallState.TRANSFERRING, CallState.ENDED, CallState.ERROR],
    CallState.LISTENING: [CallState.THINKING, CallState.SPEAKING, CallState.ON_HOLD, CallState.TRANSFERRING, CallState.ENDED, CallState.ERROR],
    CallState.THINKING: [CallState.SPEAKING, CallState.LISTENING, CallState.ENDED, CallState.ERROR],
    CallState.SPEAKING: [CallState.LISTENING, CallState.THINKING, CallState.ON_HOLD, CallState.TRANSFERRING, CallState.ENDED, CallState.ERROR],
    CallState.ON_HOLD: [CallState.CONNECTED, CallState.LISTENING, CallState.ENDED, CallState.ERROR],
    CallState.TRANSFERRING: [CallState.TRANSFERRED, CallState.CONNECTED, CallState.LISTENING, CallState.ERROR],
    CallState.TRANSFERRED: [CallState.ENDED],
    CallState.ENDED: [],
    CallState.ERROR: [CallState.ENDED],
}


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass
class CallSession:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    phone_number: str = ""
    direction: CallDirection = CallDirection.INBOUND
    state: CallState = CallState.IDLE
    language: str = "bn-BD"
    detected_language: Optional[str] = None
    language_confidence: float = 1.0
    agent_id: str = "ai-receptionist-01"
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def transition_to(self, new_state: CallState) -> None:
        allowed = VALID_TRANSITIONS.get(self.state, [])
        if new_state not in allowed and new_state != CallState.ERROR and new_state != CallState.ENDED:
            raise ValueError(
                f"Invalid state transition from {self.state.value} to {new_state.value}. Allowed: {[s.value for s in allowed]}"
            )
        self.state = new_state
        if new_state == CallState.CONNECTED and not self.answered_at:
            self.answered_at = datetime.now(timezone.utc)
        elif new_state in (CallState.ENDED, CallState.ERROR):
            if not self.ended_at:
                self.ended_at = datetime.now(timezone.utc)
                answered = ensure_utc(self.answered_at)
                started = ensure_utc(self.started_at)
                if answered:
                    self.duration = max(0, int((self.ended_at - answered).total_seconds()))
                elif started:
                    self.duration = max(0, int((self.ended_at - started).total_seconds()))


class TelephonyProvider(ABC):
    """Abstract interface for all Telephony Providers (Mock, Asterisk/FreePBX ARI, etc.)."""

    def __init__(self) -> None:
        self._event_handlers: List[Callable[[str, Dict[str, Any]], Coroutine[Any, Any, None]]] = []

    def register_event_handler(
        self, handler: Callable[[str, Dict[str, Any]], Coroutine[Any, Any, None]]
    ) -> None:
        self._event_handlers.append(handler)

    async def emit_event(self, event_name: str, data: Dict[str, Any]) -> None:
        for handler in self._event_handlers:
            try:
                await handler(event_name, data)
            except Exception as e:
                # Keep emission non-blocking
                pass

    @abstractmethod
    async def make_call(
        self, destination: str, caller_id: Optional[str] = None, call_id: Optional[str] = None
    ) -> CallSession:
        pass

    @abstractmethod
    async def answer_call(self, call_id: str) -> CallSession:
        pass

    @abstractmethod
    async def hangup_call(self, call_id: str, reason: str = "normal") -> CallSession:
        pass

    @abstractmethod
    async def hold_call(self, call_id: str) -> CallSession:
        pass

    @abstractmethod
    async def resume_call(self, call_id: str) -> CallSession:
        pass

    @abstractmethod
    async def transfer_call(self, call_id: str, target_extension: str) -> CallSession:
        pass

    @abstractmethod
    async def get_call_status(self, call_id: str) -> Optional[CallSession]:
        pass

    @abstractmethod
    async def get_active_calls(self) -> List[CallSession]:
        pass
