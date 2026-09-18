import asyncio
import random
from typing import AsyncIterator, List, Optional

from .base import STTProvider, STTResult

SAMPLE_PHRASES_BN = [
    "আসসালামু আলাইকুম, আপনাদের অফিস কখন খোলা?",
    "আমার একটা পার্সেল আসার কথা ছিল, সেটার ডেলিভারি স্ট্যাটাস কি?",
    "ভাই আমার অর্ডারটা কবে ডেলিভার হবে?",
    "আমি একজন কাস্টমার কেয়ার প্রতিনিধির সাথে কথা বলতে চাই।",
    "আপনাদের সেবা অনেক ভালো লেগেছে, ধন্যবাদ।",
]

SAMPLE_PHRASES_EN = [
    "Hello, what are your opening hours today?",
    "I'd like to check the delivery status of my package.",
    "Could you please transfer me to a human representative?",
    "Thank you very much for your help!",
]


class MockSTTProvider(STTProvider):
    """
    Mock STT Provider for testing and local dev.
    Returns realistic bilingual phrases with simulated processing latency.
    """

    def __init__(self, default_language: str = "bn-BD", simulated_latency_ms: int = 140) -> None:
        self.default_language = default_language
        self.simulated_latency_ms = simulated_latency_ms

    async def transcribe_audio(
        self, audio_data: bytes, language_hint: Optional[str] = None
    ) -> STTResult:
        await asyncio.sleep(self.simulated_latency_ms / 1000.0)
        lang = language_hint or self.default_language
        if lang.startswith("bn"):
            text = random.choice(SAMPLE_PHRASES_BN)
        else:
            text = random.choice(SAMPLE_PHRASES_EN)

        return STTResult(
            text=text,
            language=lang,
            confidence=0.96,
            latency_ms=self.simulated_latency_ms,
            is_final=True,
        )

    async def stream_transcribe(
        self, audio_stream: AsyncIterator[bytes], language_hint: Optional[str] = None
    ) -> AsyncIterator[STTResult]:
        async for _ in audio_stream:
            res = await self.transcribe_audio(b"", language_hint=language_hint)
            yield res
            break
