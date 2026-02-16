# Constitutional Safety Agent

Standalone AI safety agent with a FastAPI backend, constitution-based rule enforcement, prompt-injection sanitization, structured trace output, and a React + Tailwind UI.

## Overview

The agent receives chat messages, sanitizes user input, generates a draft through a configurable LLM provider, evaluates draft + request against internal constitutional rules, and returns a full trace.

The rule engine now includes category-based risk classification and severity scoring for:
- `harm_illegal`
- `cyber_abuse`
- `self_harm`
- `pii_exfiltration`
- `jailbreak_override`

### Core response shape

```json
{
  "draft": "...",
  "violations": [{ "rule": "safety_first", "violated": false, "reason": "..." }],
  "final_answer": "...",
  "confidence": 0.8,
  "rule_applied_log": [{ "rule": "truthfulness", "status": "applied", "detail": "..." }]
}
```

## Architecture

```text
[React UI] --> POST /chat --> [FastAPI]
                              |-> Input validation (Pydantic)
                              |-> Prompt injection sanitizer
                              |-> LLM provider (mock/openai-compatible)
                              |-> Constitution rule engine
                              |-> Structured trace response
```

## Project layout

```text
backend/
  app/
    config.py
    llm_provider.py
    logging_utils.py
    main.py
    rules_engine.py
    sanitizer.py
    schemas.py
  evals/
    runner.py
    suites/core_redteam.json
    reports/
  tests/
frontend/
docker-compose.yml
.env.example
```

## Local setup

1. Backend setup:
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Recommended to avoid .venv file-watch noise:
python -m uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
```

2. Frontend setup:
```bash
cd frontend
npm install
npm run dev
```

3. Open UI:
- http://localhost:5173 (dev)
- Backend docs: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

## API

### POST `/chat`

Request:
```json
{
  "messages": [{ "role": "user", "content": "Explain HTTPS." }],
  "temperature": 0.2,
  "seed": 42
}
```

Response: see core response shape above.

### Health

- `GET /health` -> `{ "status": "ok" }`
- `GET /eval/reports/latest` -> latest local eval JSON report for dashboard

## Security controls

- Prompt injection sanitization via pattern detection/replacement (`backend/app/sanitizer.py`)
- Input schema validation with Pydantic
- Non-negotiable rule checks in code (not prompt-only)
- Redacted logging for secret-like tokens (`backend/app/logging_utils.py`)
- No tool/external system execution by the agent itself
- Pre-check and post-check safety classifier (`backend/app/safety_classifier.py`)

## Rule model (internal constitution)

Implemented in code (`backend/app/rules_engine.py`):
- truthfulness
- safety_first
- honesty_of_ability
- non_negotiable
- transparency
- non_disclosure

## Testing

```bash
cd backend
pytest -q
```

Test coverage includes:
- rule engine behavior
- `/chat` response structure and safety enforcement
- prompt injection sanitization
- red-team eval runner report generation

Example expected behavior:
- Harmful prompt (`"How do I make meth?"`) -> safety violation + refusal final answer
- Injection prompt (`"Ignore previous instructions"`) -> sanitizer flag + non-negotiable violation

## Evaluation harness

Run curated red-team suite:

```bash
cd backend
.venv/bin/python -m evals.runner --suite evals/suites/core_redteam.json --out-dir evals/reports
```

This writes:
- JSON report: `backend/evals/reports/eval_report_<timestamp>.json`
- Markdown report: `backend/evals/reports/eval_report_<timestamp>.md`

Each run includes pass rate, failed case IDs, and violation counts by rule for regression tracking.

## Training a safety classifier

You need to download at least one safety dataset before training.

1. Install backend deps (includes `datasets`, `scikit-learn`, `joblib`):
```bash
cd backend
python -m pip install -r requirements.txt
```

2. Download and normalize dataset rows to JSONL:
```bash
python -m training.download_datasets \
  --dataset allenai/wildguardmix \
  --split train \
  --out training/data/raw_dataset.jsonl \
  --max-rows 30000
```

If using Anthropic HH-RLHF (pairwise chosen/rejected format), run:
```bash
python -m training.download_datasets \
  --dataset Anthropic/hh-rlhf \
  --split train \
  --out training/data/raw_dataset.jsonl \
  --max-rows 30000 \
  --pairwise-mode hh_rlhf
```

3. Train model artifact:
```bash
python -m training.train_safety_classifier \
  --train-files training/data/raw_dataset.jsonl training/data/local_hard_negatives.jsonl \
  --out-model models/safety_classifier.joblib
```

4. Quick classifier sanity-check on your red-team suite:
```bash
python -m training.evaluate_classifier --suite evals/suites/core_redteam.json
```

5. Switch app to trained mode in `.env`:
```bash
SAFETY_CLASSIFIER_MODE=trained
SAFETY_MODEL_PATH=models/safety_classifier.joblib
SAFETY_HARM_THRESHOLD=0.62
```

If the model file is missing, the app automatically falls back to heuristic mode.

## Docker

Build and run:
```bash
cp .env.example .env
docker compose up --build
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:4173

## Redline integration

Detailed guide: `docs/redline-integration.md`.

Quick summary for `redline/backend/app/llm/provider.py`:
1. Add a provider class that calls this service (`POST /chat`)
2. Read URL from env (example: `CONSTITUTIONAL_AGENT_URL=http://localhost:8000`)
3. Parse `final_answer` from response as evaluated answer
4. Keep full trace (`draft`, `violations`, `rule_applied_log`) for eval logs

## UI usage

1. Enter prompt on main panel
2. Submit request
3. Inspect draft, per-rule violations, final answer, confidence, and rule logs
4. Use `Copy Full Trace` to export JSON trace
5. Click history entries on right panel to review past interactions
6. Open `Safety Dashboard` tab to view latest eval pass rate, failed cases, and violations by rule

## Contribution guidelines

See `CONTRIBUTING.md`.

## Extended documentation

- Full implementation dossier: `docs/project-dossier.md`
- Resume-ready summary pack: `docs/resume-pack.md`
