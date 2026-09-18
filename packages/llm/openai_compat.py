import json
import time
from typing import Any, AsyncIterator, List
import httpx

from .base import LLMMessage, LLMProvider, LLMResponse


class OpenAICompatibleLLMProvider(LLMProvider):
    """
    OpenAI-compatible LLM Provider (OpenAI, OpenRouter, Groq, Ollama, vLLM).
    """

    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate_response(
        self, messages: List[LLMMessage], **kwargs: Any
    ) -> LLMResponse:
        start = time.perf_counter()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.4),
            "max_tokens": kwargs.get("max_tokens", 150),
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            latency = int((time.perf_counter() - start) * 1000)

            choice = data["choices"][0]
            return LLMResponse(
                content=choice["message"]["content"],
                latency_ms=latency,
                model=self.model,
                finish_reason=choice.get("finish_reason", "stop"),
                usage=data.get("usage", {}),
            )

    async def stream_response(
        self, messages: List[LLMMessage], **kwargs: Any
    ) -> AsyncIterator[str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.4),
            "max_tokens": kwargs.get("max_tokens", 150),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            async with client.stream(
                "POST", f"{self.base_url}/chat/completions", headers=headers, json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        raw = line[6:].strip()
                        if raw == "[DONE]":
                            break
                        chunk = json.loads(raw)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
