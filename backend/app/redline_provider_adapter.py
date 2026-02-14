"""
Example adapter to use Constitutional Safety Agent as a provider inside Redline.
Copy the class logic into Redline's `backend/app/llm/provider.py` and wire it in
provider selection config.
"""

from __future__ import annotations

import os

import httpx


class ConstitutionalSafetyProvider:
    def __init__(self) -> None:
        self.base_url = os.getenv("CONSTITUTIONAL_AGENT_URL", "http://localhost:8000")
        self.timeout = float(os.getenv("CONSTITUTIONAL_AGENT_TIMEOUT", "30"))

    async def generate(self, prompt: str, temperature: float = 0.2, seed: int | None = 42) -> str:
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "seed": seed,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        # Redline usually expects one answer string for scoring.
        return data["final_answer"]
