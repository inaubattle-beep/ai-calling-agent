import time
from typing import AsyncIterator, Optional
import httpx

from .base import TTSProvider, TTSResult


class OpenAICompatibleTTSProvider(TTSProvider):
    """
    OpenAI-compatible TTS Provider (OpenAI TTS, Azure speech, or custom endpoints).
    """

    def __init__(
        self,
        api_key: str = "",
        model: str = "tts-1",
        default_voice: str = "alloy",
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.default_voice = default_voice
        self.base_url = base_url.rstrip("/")

    async def synthesize(
        self, text: str, voice: Optional[str] = None, language: Optional[str] = None
    ) -> TTSResult:
        start = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": text,
            "voice": voice or self.default_voice,
            "response_format": "wav",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/audio/speech",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            audio_bytes = resp.content
            latency = int((time.perf_counter() - start) * 1000)

            # Estimate duration based on PCM WAV header
            duration_ms = max(500, int((len(audio_bytes) - 44) / 32))

            return TTSResult(
                audio_data=audio_bytes,
                format="wav",
                sample_rate=16000,
                latency_ms=latency,
                duration_ms=duration_ms,
            )

    async def stream_synthesize(
        self, text: str, voice: Optional[str] = None, language: Optional[str] = None
    ) -> AsyncIterator[bytes]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": text,
            "voice": voice or self.default_voice,
            "response_format": "pcm",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            async with client.stream(
                "POST", f"{self.base_url}/audio/speech", headers=headers, json=payload
            ) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=4096):
                    yield chunk
