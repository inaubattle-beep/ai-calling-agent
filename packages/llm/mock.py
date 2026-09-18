import asyncio
import re
from typing import Any, AsyncIterator, List

from .base import LLMMessage, LLMProvider, LLMResponse


def detect_language(text: str) -> str:
    # Bengali unicode block: \u0980-\u09FF
    if re.search(r"[\u0980-\u09FF]", text):
        return "bn-BD"
    # Banglish keywords
    banglish_words = ["bhai", "kobe", "ashbe", "amar", "apnader", "dhonnobad", "kemon", "ache"]
    lower = text.lower()
    if any(w in lower for w in banglish_words):
        return "mixed"
    return "en-US"


class MockLLMProvider(LLMProvider):
    """
    Mock LLM Provider producing realistic telephone receptionist responses in Bangla & English.
    """

    def __init__(self, model: str = "mock-receptionist-v1", simulated_latency_ms: int = 220) -> None:
        self.model = model
        self.simulated_latency_ms = simulated_latency_ms

    def _generate_text(self, messages: List[LLMMessage]) -> str:
        last_user = ""
        for m in reversed(messages):
            if m.role == "user":
                last_user = m.content
                break

        lang = detect_language(last_user)
        user_lower = last_user.lower()

        if lang == "bn-BD":
            if "সময়" in last_user or "খোলা" in last_user or "কখন" in last_user:
                return "আমাদের অফিস রবিবার থেকে বৃহস্পতিবার, সকাল ৯টা থেকে সন্ধ্যা ৬টা পর্যন্ত খোলা থাকে।"
            elif "ডেলিভারি" in last_user or "অর্ডার" in last_user or "পার্সেল" in last_user:
                return "আপনার অর্ডারটি বর্তমানে ট্রানজিটে রয়েছে। আগামী ২৪ থেকে ৪৮ ঘণ্টার মধ্যে ডেলিভারি সম্পন্ন হবে।"
            elif "কর্মকর্তা" in last_user or "প্রতিনিধি" in last_user or "ট্রান্সফার" in last_user:
                return "অবশ্যই, আমি আপনাকে আমাদের সিনিয়র কাস্টমার প্রতিনিধির কাছে ট্রান্সফার করে দিচ্ছি। অনুগ্রহ করে এক মুহূর্ত অপেক্ষা করুন।"
            elif "ধন্যবাদ" in last_user:
                return "আপনাকেও অনেক ধন্যবাদ! আপনার দিনটি শুভ হোক।"
            else:
                return "ধন্যবাদ কল করার জন্য। আমি আমাদের এআই রিসেপশনিস্ট বলছি। আপনাকে কীভাবে সহায়তা করতে পারি?"

        elif lang == "mixed":
            if "order" in user_lower or "delivery" in user_lower or "kobe" in user_lower:
                return "আপনার orderটি dispatch হয়ে গিয়েছে, খুব শীঘ্রই deliver হয়ে যাবে ভাই।"
            elif "representative" in user_lower or "kotha" in user_lower:
                return "জি ভাই, আমি এক মুহূর্তের মধ্যে আমাদের প্রতিনিধির সাথে transfer করে দিচ্ছি।"
            else:
                return "জি বলুন, কীভাবে সাহায্য করতে পারি?"

        else:
            if "hour" in user_lower or "open" in user_lower or "time" in user_lower:
                return "Our offices are open Sunday through Thursday from 9:00 AM to 6:00 PM."
            elif "order" in user_lower or "delivery" in user_lower or "package" in user_lower:
                return "Your order is currently in transit and is scheduled for delivery within 24 to 48 hours."
            elif "human" in user_lower or "representative" in user_lower or "transfer" in user_lower:
                return "Certainly, I am transferring your call to a customer representative right now. Please hold for a moment."
            elif "thank" in user_lower:
                return "You are very welcome! Have a wonderful day."
            else:
                return "Thank you for calling. This is our AI Receptionist. How may I assist you today?"

    async def generate_response(
        self, messages: List[LLMMessage], **kwargs: Any
    ) -> LLMResponse:
        await asyncio.sleep(self.simulated_latency_ms / 1000.0)
        content = self._generate_text(messages)
        return LLMResponse(
            content=content,
            latency_ms=self.simulated_latency_ms,
            model=self.model,
            usage={"prompt_tokens": 45, "completion_tokens": 25, "total_tokens": 70},
        )

    async def stream_response(
        self, messages: List[LLMMessage], **kwargs: Any
    ) -> AsyncIterator[str]:
        content = self._generate_text(messages)
        words = content.split(" ")
        for word in words:
            await asyncio.sleep(0.04)
            yield word + " "
