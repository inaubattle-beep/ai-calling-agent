import asyncio
import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

from packages.agent_core.agent import Agent, AgentConfig
from packages.stt.base import STTProvider, STTResult
from packages.tts.base import TTSProvider


def load_pipeline_class():
    source_dir = Path(__file__).parents[1] / "services" / "voice-runtime" / "src"
    package_name = "voice_runtime_test_package"
    package = importlib.util.module_from_spec(
        importlib.util.spec_from_loader(package_name, loader=None, is_package=True)
    )
    package.__path__ = [str(source_dir)]
    sys.modules[package_name] = package
    return importlib.import_module(f"{package_name}.pipeline").VoicePipeline


class DeterministicSTT(STTProvider):
    async def transcribe_audio(self, audio_data: bytes, language_hint=None) -> STTResult:
        return STTResult(text="Hello from the caller", language=language_hint or "en-US")

    async def stream_transcribe(self, audio_stream, language_hint=None):
        if False:
            yield None


class DeterministicTTS(TTSProvider):
    def __init__(self, block=False):
        self.block = block
        self.started = asyncio.Event()
        self.cancelled = False

    async def synthesize(self, text, voice=None, language=None):
        raise NotImplementedError

    async def stream_synthesize(self, text, voice=None, language=None):
        self.started.set()
        yield b"audio"
        if self.block:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.cancelled = True
                raise


class DeterministicAgent(Agent):
    def __init__(self):
        super().__init__(AgentConfig(default_language="en-US"))
        self.is_speaking = False
        self.current_language = "en-US"
        self.processed = []
        self.interrupted = False

    async def start_call(self, call_id, caller_number):
        return "Welcome"

    async def process_speech(self, call_id, speech_text):
        self.processed.append(speech_text)
        return "How can I help?"

    async def handle_interruption(self, call_id):
        self.interrupted = True

    async def end_call(self, call_id):
        return None


def pcm_frame(amplitude=0):
    sample = int(amplitude).to_bytes(2, "little", signed=True)
    return sample * 320


@pytest.mark.asyncio
async def test_voice_pipeline_processes_utterance_and_emits_tts():
    VoicePipeline = load_pipeline_class()
    agent = DeterministicAgent()
    audio = []
    pipeline = VoicePipeline(
        stt=DeterministicSTT(),
        agent=agent,
        tts=DeterministicTTS(),
        on_audio_out=audio.append,
        call_id="call-1",
    )

    for _ in range(2):
        await pipeline.feed_audio_frame(pcm_frame(1000))
    for _ in range(9):
        await pipeline.feed_audio_frame(pcm_frame())
    await pipeline.wait_for_idle()

    assert agent.processed == ["Hello from the caller"]
    assert audio == [b"audio"]


@pytest.mark.asyncio
async def test_voice_pipeline_cancels_tts_on_barge_in():
    VoicePipeline = load_pipeline_class()
    agent = DeterministicAgent()
    tts = DeterministicTTS(block=True)
    pipeline = VoicePipeline(stt=DeterministicSTT(), agent=agent, tts=tts)
    tts_task = asyncio.create_task(pipeline._speak("Please wait"))
    await asyncio.sleep(0.05)
    assert tts.started.is_set()
    assert pipeline.barge_in.ai_is_speaking is True

    await pipeline.feed_audio_frame(pcm_frame(1000))
    await pipeline.feed_audio_frame(pcm_frame(1000))
    await pipeline.feed_audio_frame(pcm_frame(1000))
    assert pipeline.barge_in._triggered is True
    await asyncio.sleep(0.05)

    await asyncio.sleep(0)
    assert tts_task.done()
    assert tts_task.cancelled()
    assert tts.cancelled is True
    assert agent.interrupted is True