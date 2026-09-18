import pytest
from packages.telephony.mock import MockTelephonyProvider
from packages.telephony.base import CallState
from packages.stt.mock import MockSTTProvider
from packages.tts.mock import MockTTSProvider
from packages.llm.mock import MockLLMProvider, LLMMessage


@pytest.mark.asyncio
async def test_mock_telephony_lifecycle():
    provider = MockTelephonyProvider()
    events = []

    async def on_event(name, data):
        events.append((name, data))

    provider.register_event_handler(on_event)

    call = await provider.make_call("+8801712345678")
    assert call.phone_number == "+8801712345678"
    assert call.state == CallState.DIALING

    # Answer call
    call = await provider.answer_call(call.id)
    assert call.state == CallState.LISTENING

    # Update state to thinking and speaking
    call = await provider.update_state(call.id, CallState.THINKING)
    assert call.state == CallState.THINKING

    call = await provider.update_state(call.id, CallState.SPEAKING)
    assert call.state == CallState.SPEAKING

    # Hangup
    call = await provider.hangup_call(call.id)
    assert call.state == CallState.ENDED


@pytest.mark.asyncio
async def test_mock_stt_tts():
    stt = MockSTTProvider()
    res_stt = await stt.transcribe_audio(b"fake_pcm", language_hint="bn-BD")
    assert len(res_stt.text) > 0
    assert res_stt.language == "bn-BD"

    tts = MockTTSProvider()
    res_tts = await tts.synthesize("আমাদের অফিস খোলা আছে।", language="bn-BD")
    assert len(res_tts.audio_data) > 44  # Valid WAV header + PCM
    assert res_tts.duration_ms > 0
