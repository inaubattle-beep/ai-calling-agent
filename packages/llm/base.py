from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional


@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    latency_ms: int = 250
    model: str = "mock-llm"
    finish_reason: str = "stop"
    usage: Dict[str, int] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract LLM Provider interface."""

    @abstractmethod
    async def generate_response(
        self, messages: List[LLMMessage], **kwargs: Any
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def stream_response(
        self, messages: List[LLMMessage], **kwargs: Any
    ) -> AsyncIterator[str]:
        pass
