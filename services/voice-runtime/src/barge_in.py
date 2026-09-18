import asyncio
import logging
from typing import Callable, Coroutine, Optional

from .vad import VoiceActivityDetector

logger = logging.getLogger("voice.barge_in")


class BargeInCoordinator:
    """
    Monitors incoming caller audio frames while AI is speaking.
    If speech energy exceeds threshold, triggers immediate interruption callback.
    """

    def __init__(
        self,
        vad: Optional[VoiceActivityDetector] = None,
        on_interruption: Optional[Callable[[], Coroutine[None, None, None]]] = None,
    ) -> None:
        self.vad = vad or VoiceActivityDetector()
        self.on_interruption = on_interruption
        self.ai_is_speaking = False
        self._triggered = False

    def set_ai_speaking(self, speaking: bool) -> None:
        self.ai_is_speaking = speaking
        if not speaking:
            self._triggered = False

    async def process_incoming_frame(self, frame_bytes: bytes) -> bool:
        """
        Returns True if barge-in was triggered on this frame.
        """
        if not self.ai_is_speaking or self._triggered:
            return False

        _, speech_started = self.vad.process_frame(frame_bytes)
        if speech_started:
            logger.info("Caller barge-in detected! Aborting AI speech.")
            self._triggered = True
            self.ai_is_speaking = False
            if self.on_interruption:
                await self.on_interruption()
            return True

        return False
