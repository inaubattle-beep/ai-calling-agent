import pytest
from packages.agent_core.language import LanguageDetector
from packages.agent_core.receptionist import AIReceptionistAgent
from packages.llm.mock import MockLLMProvider


def test_language_detector():
    detector = LanguageDetector()

    # Bangla
    bn_res = detector.detect("আসসালামু আলাইকুম, আপনাদের অফিস কখন খোলা?")
    assert bn_res.code == "bn-BD"
    assert bn_res.confidence > 0.8

    # English
    en_res = detector.detect("Hello, what time do you close today?")
    assert en_res.code == "en-US"

    # Banglish / Mixed
    mixed_res = detector.detect("Bhai amar order delivery kobe hobe?")
    assert mixed_res.code == "mixed"


@pytest.mark.asyncio
async def test_receptionist_agent_flow():
    llm = MockLLMProvider()
    agent = AIReceptionistAgent(llm_provider=llm)

    # 1. Start call (Greeting)
    greeting = await agent.start_call("call-123", "+8801700000000")
    assert "আসসালামু আলাইকুম" in greeting
    assert len(agent.conversation_history) == 1

    # 2. Process Bangla customer inquiry
    resp_bn = await agent.process_speech("call-123", "আপনাদের অফিস কখন খোলা?")
    assert len(resp_bn) > 0
    assert "**" not in resp_bn
    assert "#" not in resp_bn
    assert len(agent.conversation_history) == 3

    # 3. Process English customer inquiry
    resp_en = await agent.process_speech("call-123", "Could you transfer me to a human representative?")
    assert "transfer" in resp_en.lower() or "representative" in resp_en.lower()

    # 4. Caller barge-in
    await agent.handle_interruption("call-123")
    assert agent.is_speaking is False
