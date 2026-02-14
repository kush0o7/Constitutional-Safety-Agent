from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from .config import settings


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, temperature: float, seed: int | None) -> str:
        raise NotImplementedError


class MockProvider(LLMProvider):
    async def generate(self, prompt: str, temperature: float, seed: int | None) -> str:
        return f"Draft response based on sanitized input: {prompt[:500]}"


class OpenAICompatibleProvider(LLMProvider):
    async def generate(self, prompt: str, temperature: float, seed: int | None) -> str:
        if not settings.llm_api_key:
            raise RuntimeError("LLM_API_KEY is required for openai_compatible provider")

        payload = {
            "model": settings.llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a cautious assistant. Follow platform safety policy.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        if seed is not None:
            payload["seed"] = seed

        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            resp = await client.post(f"{settings.llm_api_base}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"]


def get_provider() -> LLMProvider:
    provider = settings.llm_provider.lower().strip()
    if provider == "mock":
        return MockProvider()
    if provider == "openai_compatible":
        return OpenAICompatibleProvider()
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
