import asyncio
import logging
from typing import AsyncIterator, Callable, Coroutine, Optional

from packages.agent_core.agent import Agent
from packages.stt.base import STTProvider
from packages.tts.base import TTSProvider
from .barge_in import BargeInCoordinator
from .vad import VoiceActivityDetector

logger = logging.getLogger("voice.pipeline")


class VoicePipeline:
    """
    RTP/Audio Stream -> VAD -> STT -> Agent -> TTS -> RTP Pipeline.
    Supports streaming and caller interruption / barge-in.
    """

    def __init__(
        self,
        stt: STTProvider,
        agent: Agent,
        tts: TTSProvider,
        on_audio_out: Optional[Callable[[bytes], Coroutine[None, None, None]]] = None,
    ) -> None:
        self.stt = stt
        self.agent = agent
        self.tts = tts
        self.on_audio_out = on_audio_out
        self.vad = VoiceActivityDetector()
        self.barge_in = BargeInCoordinator(vad=self.vad, on_interruption=self._handle_interruption)
        self.is_active = False

    async def _handle_interruption(self) -> None:
        logger.info("Voice pipeline received barge-in interruption.")
        await self.agent.handle_interruption(call_id="active-call")

    async def feed_audio_frame(self, frame_bytes: bytes) -> None:
        """Processes an incoming RTP frame from caller."""
        # Check barge-in if agent is speaking
        interrupted = await self.barge_in.process_incoming_frame(frame_bytes)
        if interrupted:
            return
