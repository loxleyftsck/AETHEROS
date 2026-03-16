"""
LLM Backbone – OpenAI + Ollama unified interface with streaming and tool calls.
"""

import json
from typing import AsyncGenerator, Optional
import httpx
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class LLMBackbone:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or (
            settings.OPENAI_MODEL if self.provider == "openai" else settings.OLLAMA_MODEL
        )
        self._total_tokens = 0

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        tools: Optional[list[dict]] = None,
        response_format: Optional[dict] = None,
    ) -> dict:
        if self.provider == "openai":
            return await self._openai_chat(messages, temperature, max_tokens, tools, response_format)
        return await self._ollama_chat(messages, temperature, max_tokens)

    async def stream_chat(self, messages: list[dict], temperature: float = 0.3) -> AsyncGenerator[str, None]:
        if self.provider == "openai":
            async for token in self._openai_stream(messages, temperature):
                yield token
        else:
            async for token in self._ollama_stream(messages, temperature):
                yield token

    async def _openai_chat(self, messages, temperature, max_tokens, tools, response_format) -> dict:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        kwargs = dict(model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if response_format:
            kwargs["response_format"] = response_format

        for attempt in range(3):
            try:
                resp = await client.chat.completions.create(**kwargs)
                tokens = resp.usage.total_tokens if resp.usage else 0
                self._total_tokens += tokens
                choice = resp.choices[0]
                tool_calls = []
                if choice.message.tool_calls:
                    for tc in choice.message.tool_calls:
                        tool_calls.append({"id": tc.id, "name": tc.function.name, "args": json.loads(tc.function.arguments)})
                return {"content": choice.message.content or "", "tool_calls": tool_calls, "tokens": tokens}
            except Exception as e:
                logger.warning("OpenAI call failed", attempt=attempt, error=str(e))
                if attempt == 2:
                    raise
        return {"content": "", "tool_calls": [], "tokens": 0}

    async def _openai_stream(self, messages, temperature) -> AsyncGenerator[str, None]:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        stream = await client.chat.completions.create(
            model=self.model, messages=messages, temperature=temperature, stream=True
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def _ollama_chat(self, messages, temperature, max_tokens) -> dict:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False,
                      "options": {"temperature": temperature, "num_predict": max_tokens}},
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
            self._total_tokens += tokens
            return {"content": content, "tool_calls": [], "tokens": tokens}

    async def _ollama_stream(self, messages, temperature) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={"model": self.model, "messages": messages, "stream": True,
                      "options": {"temperature": temperature}}) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("message", {}).get("content", "")
                            if token:
                                yield token
                        except json.JSONDecodeError:
                            continue
