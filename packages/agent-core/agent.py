from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional


@dataclass
class ConversationTurn:
    speaker: str  # "customer" or "ai" or "system"
    text: str
    language: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: Optional[int] = None


@dataclass
class AgentConfig:
    agent_id: str = "ai-receptionist-01"
    name: str = "AI Receptionist"
    default_language: str = "bn-BD"
    model: str = "mock-receptionist-v1"
    max_response_sentences: int = 3
    enable_barge_in: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    """Abstract Base Agent Interface for Voice Agents."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.conversation_history: List[ConversationTurn] = []

    def add_turn(self, speaker: str, text: str, language: str, latency_ms: Optional[int] = None) -> ConversationTurn:
        turn = ConversationTurn(
            speaker=speaker,
            text=text,
            language=language,
            latency_ms=latency_ms,
        )
        self.conversation_history.append(turn)
        return turn

    @abstractmethod
    async def start_call(self, call_id: str, caller_number: str) -> str:
        """Called when call is connected. Returns opening greeting."""
        pass

    @abstractmethod
    async def process_speech(self, call_id: str, speech_text: str) -> str:
        """Processes caller utterance, detects language, and generates response."""
        pass

    @abstractmethod
    async def handle_interruption(self, call_id: str) -> None:
        """Handles caller barge-in."""
        pass

    @abstractmethod
    async def end_call(self, call_id: str) -> None:
        """Cleanup session resources."""
        pass
