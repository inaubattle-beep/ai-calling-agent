import asyncio
import io
import time
from typing import AsyncIterator, Optional
import httpx

from .base import STTProvider, STTResult


class WhisperSTTProvider(STTProvider):
    """
    OpenAI Whisper-compatible streaming/buffered STT Provider.
    Supports official OpenAI, Azure, Groq, or local vLLM/faster-whisper endpoints.
    """

    def __init__(
        self,
        api_key: str = "",
        model: str = "whisper-1",
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def transcribe_audio(
        self, audio_data: bytes, language_hint: Optional[str] = None
    ) -> STTResult:
        if not self.api_key:
            raise ValueError("WhisperSTTProvider requires an API key")

        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            files = {"file": ("audio.wav", io.BytesIO(audio_data), "audio/wav")}
            data = {"model": self.model}
            if language_hint:
                data["language"] = "bn" if language_hint.startswith("bn") else "en"

            resp = await client.post(
                f"{self.base_url}/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
            )
            resp.raise_for_status()
            res_json = resp.json()
            latency = int((time.perf_counter() - start) * 1000)

            return STTResult(
                text=res_json.get("text", ""),
                language=language_hint or "bn-BD",
                confidence=0.98,
                latency_ms=latency,
                is_final=True,
            )

    async def stream_transcribe(
        self, audio_stream: AsyncIterator[bytes], language_hint: Optional[str] = None
    ) -> AsyncIterator[STTResult]:
        buffer = bytearray()
        async for chunk in audio_stream:
            buffer.extend(chunk)
            if len(buffer) >= 32000:  # ~1 second of 16kHz audio
                res = await self.transcribe_audio(bytes(buffer), language_hint=language_hint)
                buffer.clear()
                yield res
