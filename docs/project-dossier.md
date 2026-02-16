# Project Dossier: Constitutional Safety Agent

## 1. Executive Summary

Constitutional Safety Agent is a standalone AI system designed for safe, traceable responses under explicit constitutional constraints. The project combines:
- FastAPI backend
- Rule-based constitutional enforcement
- Prompt-injection sanitization
- Pluggable LLM provider abstraction
- Trainable safety classifier pipeline
- Evaluation harness with red-team suites and report generation
- React + Tailwind frontend with trace visibility and safety dashboard

It is designed to be integrated as a provider into external evaluation systems such as Redline.

## 2. Product Goals

Primary goals:
- Prevent harmful/unsafe output by default
- Expose transparent rule outcomes in response traces
- Resist prompt-injection attempts
- Support reproducible safety evaluation over time
- Provide developer-friendly integration surface for external evaluators

Secondary goals:
- Preserve quick local setup and Docker deployment
- Keep default mode functional without paid API keys (`mock` provider)
- Enable iterative hardening through classifier training and eval suites

## 3. Scope Implemented

Completed capabilities:
- `POST /chat` with structured response payload
- `GET /health`
- `GET /eval/reports/latest` for UI dashboarding
- Internal constitution rules in code (not static prompt)
- Request sanitization against known injection patterns
- Safety rule enforcement + refusal behavior
- Confidence scoring based on rule violations
- Secure logging filter with secret redaction
- Unit tests across rule engine, sanitizer, endpoints, eval runner
- Red-team eval runner with JSON and Markdown outputs
- Safety classifier module with heuristic fallback + trained sklearn model loading
- Dataset download/normalization + training scripts
- Frontend chat UI + history + full trace copy + safety dashboard
- Dockerfiles and docker-compose orchestration
- Redline integration guidance and provider adapter sample

## 4. Architecture

High-level flow:
1. Frontend sends prompt to `POST /chat`
2. Backend validates schema with Pydantic
3. Sanitizer neutralizes injection-like content
4. Pre-safety classifier scores user content
5. LLM provider generates draft (or generation is blocked if pre-check is harmful)
6. Post-safety classifier scores draft output
7. Constitution engine evaluates violations and generates final answer
8. Structured trace is returned to frontend

Core backend modules:
- `backend/app/main.py`: API routes and orchestration
- `backend/app/schemas.py`: request/response contracts
- `backend/app/sanitizer.py`: injection pattern detection and neutralization
- `backend/app/safety_classifier.py`: heuristic + trained classifier abstraction
- `backend/app/rules_engine.py`: constitutional policy logic + confidence calculation
- `backend/app/llm_provider.py`: provider abstraction (`mock` and `openai_compatible`)
- `backend/app/logging_utils.py`: redaction filter for sensitive log content

## 5. Constitutional Rules and Enforcement

Rules enforced:
- `truthfulness`
- `safety_first`
- `honesty_of_ability`
- `non_negotiable`
- `transparency`
- `non_disclosure`

Risk categories currently modeled:
- `harm_illegal`
- `cyber_abuse`
- `fraud_deception`
- `self_harm`
- `pii_exfiltration`
- `jailbreak_override`

Behavioral outcomes:
- Harmful/illegal/fraud/cyber/self-harm requests are refused
- Real-time capability mismatch triggers cautious language
- Injection attempts trigger non-negotiable violations
- Output includes violation list and per-rule application log

## 6. Security and Safety Controls

Controls implemented:
- Input schema validation with explicit constraints
- Injection pattern sanitization before model calls
- Rule checks independent from model prompt
- Harm threshold controlled by env (`SAFETY_HARM_THRESHOLD`)
- Safe default classifier mode with fallback behavior
- Redacted logs to avoid key/token leakage
- No local filesystem/network tooling exposed to model actions

Current known limits:
- Pattern/rule coverage is finite and requires continuous expansion
- Heuristic mode can under/over-trigger on edge cases
- Binary classifier (`safe/harmful`) may conflate jailbreak and harmfulness

## 7. Evaluation and Quality Strategy

Automated test coverage:
- Endpoint contract tests
- Rule engine behavior tests
- Sanitizer behavior tests
- Eval runner tests
- Safety classifier tests

Red-team suite process:
- Cases in `backend/evals/suites/core_redteam.json`
- Run via `python -m evals.runner`
- Reports written to `backend/evals/reports/`
- Dashboard reads latest report from backend endpoint

Classifier training process:
- Dataset normalization: `training/download_datasets.py`
- Model training: `training/train_safety_classifier.py`
- Sanity evaluation: `training/evaluate_classifier.py`
- Local hard negatives: `training/data/local_hard_negatives.jsonl`

## 8. Frontend UX Features

Implemented interface:
- Chat tab with prompt entry and submit
- Trace card showing draft, violations, final answer, confidence, rule log
- Copy full trace button
- Prompt history sidebar
- Safety Dashboard tab with:
- pass rate
- total/passed/failed cards
- violations-by-rule view
- failed case IDs
- report metadata

## 9. Deployment and Operations

Local run modes:
- Native Python + Node
- Docker compose for backend + frontend

Config strategy:
- `.env`-driven configuration
- reasonable defaults for local development
- provider and safety settings controlled without code edits

Operational notes:
- Use `--reload-dir app` in backend dev mode to avoid `.venv` watch churn
- Prefer `.venv/bin/python -m ...` for version-consistent training/evaluation

## 10. Redline Integration Status

Available artifacts:
- Integration guide: `docs/redline-integration.md`
- Adapter example: `backend/app/redline_provider_adapter.py`

Integration model:
- Redline custom provider forwards messages to this backend `/chat`
- Redline consumes `final_answer`
- Trace fields can be stored as metadata for analysis

## 11. Future Improvements Roadmap

High-priority:
- Multi-class safety classifier (`safe`, `harmful`, `jailbreak`, `fraud`, `self_harm`)
- Better threshold calibration and per-class thresholds
- Add uncertainty and citation-aware scoring for factual tasks
- Expand red-team suite breadth and multilingual coverage
- Persist traces/eval reports in DB with trend charts

Medium-priority:
- Streaming responses with incremental safety guardrails
- Stronger classifier explainability (top features, rationale slices)
- More robust model registry/versioning for trained artifacts

## 12. Repository Artifacts Index

Primary docs:
- `README.md`
- `CONTRIBUTING.md`
- `docs/redline-integration.md`
- `docs/project-dossier.md`
- `docs/resume-pack.md`

Safety/eval/training code:
- `backend/app/rules_engine.py`
- `backend/app/safety_classifier.py`
- `backend/evals/runner.py`
- `backend/training/download_datasets.py`
- `backend/training/train_safety_classifier.py`
- `backend/training/evaluate_classifier.py`

Frontend:
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/src/types.ts`

