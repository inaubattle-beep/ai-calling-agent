import asyncio
import logging
from typing import Optional

from packages.llm.base import LLMMessage, LLMProvider
from .agent import Agent, AgentConfig, ConversationTurn
from .language import LanguageDetector

logger = logging.getLogger("agent.receptionist")

SYSTEM_PROMPT = """You are a polite, helpful, and professional telephone AI Receptionist for a business in Bangladesh.

TELEPHONE GUIDELINES:
1. Always respond in the language the caller speaks:
   - If the caller speaks Bangla (bn-BD), respond in clear, polite Bangla.
   - If the caller speaks English (en-US), respond in polite English.
   - If the caller speaks Banglish or mixed code-switching, respond naturally in mixed or polite Bangla.
2. Keep all responses brief and natural for phone audio: strictly 1 to 3 sentences.
3. Absolutely NO markdown syntax (no asterisks, bold, bullet points, numbered lists, or URLs).
4. Do not invent or hallucinate customer orders or private details. If unknown, ask politely for their phone or tracking number.
5. If the caller asks for a human representative, confirm politely and mention they are being transferred.
"""


class AIReceptionistAgent(Agent):
    """
    Bilingual AI Receptionist Agent supporting Bangla (bn-BD) and English (en-US).
    """

    def __init__(self, llm_provider: LLMProvider, config: Optional[AgentConfig] = None) -> None:
        cfg = config or AgentConfig(
            agent_id="ai-receptionist-01",
            name="AI Receptionist",
            default_language="bn-BD",
        )
        super().__init__(cfg)
        self.llm = llm_provider
        self.detector = LanguageDetector()
        self.current_language = cfg.default_language
        self.is_speaking = False
        self._interrupted = False

    async def start_call(self, call_id: str, caller_number: str) -> str:
        self.conversation_history.clear()
        self._interrupted = False

        # Polite bilingual opening
        greeting = "আসসালামু আলাইকুম, AI কল সেন্টারে আপনাকে স্বাগতম। আমি কীভাবে সাহায্য করতে পারি?"
        self.current_language = "bn-BD"
        self.add_turn(speaker="ai", text=greeting, language=self.current_language)
        return greeting

    async def process_speech(self, call_id: str, speech_text: str) -> str:
        # Detect caller language
        det = self.detector.detect(speech_text)
        self.current_language = det.code

        # Add customer turn
        self.add_turn(speaker="customer", text=speech_text, language=self.current_language)

        # Build message history for LLM
        messages = [LLMMessage(role="system", content=SYSTEM_PROMPT)]
        for turn in self.conversation_history[-6:]:  # Keep last 6 turns for low latency context
            role = "user" if turn.speaker == "customer" else "assistant"
            messages.append(LLMMessage(role=role, content=turn.text))

        # Generate response
        llm_resp = await self.llm.generate_response(messages)
        ai_text = llm_resp.content.strip()

        # Clean any accidental markdown
        ai_text = ai_text.replace("**", "").replace("*", "").replace("#", "").replace("`", "")

        # Add AI turn
        self.add_turn(
            speaker="ai",
            text=ai_text,
            language=self.current_language,
            latency_ms=llm_resp.latency_ms,
        )

        return ai_text

    async def handle_interruption(self, call_id: str) -> None:
        logger.info(f"Barge-in: Caller interrupted AI on call {call_id}")
        self._interrupted = True
        self.is_speaking = False
        # Add system event to conversation
        self.add_turn(
            speaker="system",
            text="[Caller interrupted AI speech]",
            language=self.current_language,
        )

    async def end_call(self, call_id: str) -> None:
        self.is_speaking = False
        self._interrupted = False
