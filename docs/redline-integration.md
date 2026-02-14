# Redline Provider Integration

This project can be consumed by Redline as a configurable provider.

## 1. Environment variables

Add in Redline backend environment:

```bash
CONSTITUTIONAL_AGENT_URL=http://localhost:8000
CONSTITUTIONAL_AGENT_TIMEOUT=30
```

## 2. Provider implementation

In Redline `backend/app/llm/provider.py`, add a provider similar to:

```python
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
            resp = await client.post(f"{self.base_url}/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Redline typically consumes one answer string.
        # Keep trace fields in logs/metadata if your pipeline supports it.
        return data["final_answer"]
```

## 3. Make configurable in Redline

Add provider selection entry in Redline config mapping, e.g.:

```python
PROVIDERS = {
    "openai": OpenAIProvider,
    "constitutional_safety": ConstitutionalSafetyProvider,
}
```

Set runtime config to use `constitutional_safety`.

## 4. Example Redline eval command

Run your Constitutional Safety Agent first, then execute Redline evaluation command:

```bash
# Example, adapt to your Redline CLI structure
python -m backend.app.eval.run --provider constitutional_safety --suite safety_core
```

If your Redline CLI differs, keep the same provider key and pass it through the standard `--provider` argument path.

## 5. Local preflight before Redline

Before running Redline, execute the local red-team suite:

```bash
cd backend
.venv/bin/python -m evals.runner --suite evals/suites/core_redteam.json --out-dir evals/reports
```

Use the generated report pass rate to catch regressions early.
