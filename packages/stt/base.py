from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional


@dataclass
class STTResult:
    text: str
    language: str
    confidence: float = 0.95
    latency_ms: int = 150
    is_final: bool = True


class STTProvider(ABC):
    """Abstract Speech-To-Text Provider interface."""

    @abstractmethod
    async def transcribe_audio(
        self, audio_data: bytes, language_hint: Optional[str] = None
    ) -> STTResult:
        """Transcribe an audio buffer into text."""
        pass

    @abstractmethod
    async def stream_transcribe(
        self, audio_stream: AsyncIterator[bytes], language_hint: Optional[str] = None
    ) -> AsyncIterator[STTResult]:
        """Stream transcription chunks from live audio stream."""
        pass
