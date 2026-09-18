import asyncio
import math
from typing import AsyncIterator, Optional

from .base import TTSProvider, TTSResult


def generate_mock_wav_header(data_size: int, sample_rate: int = 16000, channels: int = 1) -> bytes:
    """Generates standard 44-byte RIFF/WAV PCM header for mock audio."""
    byte_rate = sample_rate * channels * 2
    block_align = channels * 2
    total_chunk_size = 36 + data_size
    header = bytearray()
    header.extend(b"RIFF")
    header.extend(total_chunk_size.to_bytes(4, "little"))
    header.extend(b"WAVE")
    header.extend(b"fmt ")
    header.extend((16).to_bytes(4, "little"))  # Subchunk1Size
    header.extend((1).to_bytes(2, "little"))   # PCM
    header.extend(channels.to_bytes(2, "little"))
    header.extend(sample_rate.to_bytes(4, "little"))
    header.extend(byte_rate.to_bytes(4, "little"))
    header.extend(block_align.to_bytes(2, "little"))
    header.extend((16).to_bytes(2, "little"))  # 16-bit
    header.extend(b"data")
    header.extend(data_size.to_bytes(4, "little"))
    return bytes(header)


class MockTTSProvider(TTSProvider):
    """
    Mock TTS Provider for development and automated tests.
    Calculates realistic audio playback durations and yields streaming PCM chunks.
    """

    def __init__(self, simulated_latency_ms: int = 180) -> None:
        self.simulated_latency_ms = simulated_latency_ms

    async def synthesize(
        self, text: str, voice: Optional[str] = None, language: Optional[str] = None
    ) -> TTSResult:
        await asyncio.sleep(self.simulated_latency_ms / 1000.0)
        # Approximate: ~150 words per minute => ~2.5 words/sec => ~400ms per word
        word_count = max(1, len(text.split()))
        duration_ms = int(word_count * 380)
        pcm_bytes = int((16000 * 2) * (duration_ms / 1000.0))
        # Generate silence/low-level noise bytes
        data = generate_mock_wav_header(pcm_bytes) + (b"\x00\x01" * (pcm_bytes // 2))

        return TTSResult(
            audio_data=data,
            format="wav",
            sample_rate=16000,
            latency_ms=self.simulated_latency_ms,
            duration_ms=duration_ms,
        )

    async def stream_synthesize(
        self, text: str, voice: Optional[str] = None, language: Optional[str] = None
    ) -> AsyncIterator[bytes]:
        await asyncio.sleep(self.simulated_latency_ms / 1000.0)
        # Chunk into 200ms audio slices
        slice_size = 6400  # 16kHz * 2 bytes * 0.2s
        word_count = max(1, len(text.split()))
        slices = max(1, int(word_count * 2))

        for _ in range(slices):
            await asyncio.sleep(0.18)  # Real-time cadence
            yield b"\x00\x02" * (slice_size // 2)
