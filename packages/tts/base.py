from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional


@dataclass
class TTSResult:
    audio_data: bytes
    format: str = "wav"
    sample_rate: int = 16000
    latency_ms: int = 200
    duration_ms: int = 1500


class TTSProvider(ABC):
    """Abstract Text-To-Speech Provider interface."""

    @abstractmethod
    async def synthesize(
        self, text: str, voice: Optional[str] = None, language: Optional[str] = None
    ) -> TTSResult:
        pass

    @abstractmethod
    async def stream_synthesize(
        self, text: str, voice: Optional[str] = None, language: Optional[str] = None
    ) -> AsyncIterator[bytes]:
        pass
