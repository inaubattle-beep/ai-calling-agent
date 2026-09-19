import asyncio
import inspect
import logging
from typing import Any, Callable, Optional

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
        on_audio_out: Optional[Callable[[bytes], Any]] = None,
        call_id: str = "active-call",
        language_hint: Optional[str] = None,
    ) -> None:
        self.stt = stt
        self.agent = agent
        self.tts = tts
        self.on_audio_out = on_audio_out
        self.call_id = call_id
        self.language_hint = language_hint
        self.vad = VoiceActivityDetector()
        self.barge_in = BargeInCoordinator(on_interruption=self._handle_interruption)
        self.is_active = True
        self._speech_buffer = bytearray()
        self._silence_frames = 0
        self._utterance_task: Optional[asyncio.Task[None]] = None
        self._tts_task: Optional[asyncio.Task[None]] = None

    async def start(self, caller_number: str = "") -> str:
        """Start a conversation and play the agent's opening greeting."""
        self.is_active = True
        greeting = await self.agent.start_call(self.call_id, caller_number)
        await self._speak(greeting)
        return greeting

    async def stop(self) -> None:
        """Stop processing audio and clean up the agent session."""
        self.is_active = False
        for task in (self._utterance_task, self._tts_task):
            if task and not task.done():
                task.cancel()
        await self.agent.end_call(self.call_id)

    async def wait_for_idle(self) -> None:
        """Wait until the currently buffered utterance has been processed."""
        if self._utterance_task:
            await self._utterance_task

    async def _handle_interruption(self) -> None:
        logger.info("Voice pipeline received barge-in interruption.")
        await self.agent.handle_interruption(call_id=self.call_id)
        if self._tts_task and not self._tts_task.done():
            self._tts_task.cancel()

    async def _speak(self, text: str) -> None:
        self.barge_in.set_ai_speaking(True)
        self.agent.is_speaking = True  # type: ignore[attr-defined]
        self._tts_task = asyncio.current_task()
        try:
            async for audio_chunk in self.tts.stream_synthesize(
                text, language=getattr(self.agent, "current_language", self.language_hint)
            ):
                if self.on_audio_out:
                    result = self.on_audio_out(audio_chunk)
                    if inspect.isawaitable(result):
                        await result
        except asyncio.CancelledError:
            logger.info("TTS playback cancelled for call %s", self.call_id)
            raise
        finally:
            self.barge_in.set_ai_speaking(False)
            self.agent.is_speaking = False  # type: ignore[attr-defined]
            if self._tts_task is asyncio.current_task():
                self._tts_task = None

    async def _process_utterance(self, audio_data: bytes) -> None:
        result = await self.stt.transcribe_audio(audio_data, language_hint=self.language_hint)
        if not result.text.strip():
            return
        response = await self.agent.process_speech(self.call_id, result.text)
        await self._speak(response)

    def _schedule_utterance(self) -> None:
        if self._utterance_task and not self._utterance_task.done():
            return
        audio_data = bytes(self._speech_buffer)
        self._speech_buffer.clear()
        self._utterance_task = asyncio.create_task(self._process_utterance(audio_data))

    async def feed_audio_frame(self, frame_bytes: bytes) -> None:
        """Processes an incoming RTP frame from caller."""
        if not self.is_active:
            return

        # Check barge-in if agent is speaking
        interrupted = await self.barge_in.process_incoming_frame(frame_bytes)
        if interrupted:
            return

        is_speech, speech_started = self.vad.process_frame(frame_bytes)
        if speech_started:
            self._speech_buffer.clear()
            self._silence_frames = 0
        if is_speech:
            self._speech_buffer.extend(frame_bytes)
            self._silence_frames = 0
        elif self._speech_buffer:
            self._silence_frames += 1
            if self._silence_frames > 8:
                self._schedule_utterance()
