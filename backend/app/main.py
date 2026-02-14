from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .llm_provider import get_provider
from .logging_utils import configure_logging
from .rules_engine import ConstitutionEngine, RuleContext, confidence_from_violations
from .safety_classifier import get_safety_classifier
from .sanitizer import sanitize_text
from .schemas import ChatRequest, ChatResponse, LatestEvalReportResponse

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="0.1.0")

allowed_origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/eval/reports/latest", response_model=LatestEvalReportResponse)
def latest_eval_report() -> LatestEvalReportResponse:
    reports_dir = Path(settings.eval_reports_dir)
    if not reports_dir.is_absolute():
        reports_dir = Path(__file__).resolve().parents[1] / reports_dir

    report_files = sorted(reports_dir.glob("eval_report_*.json"))
    if not report_files:
        raise HTTPException(status_code=404, detail="No eval reports found")

    latest_file = report_files[-1]
    payload = json.loads(latest_file.read_text())
    payload["source_file"] = latest_file.name
    return LatestEvalReportResponse(**payload)


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    user_content = "\n".join([m.content for m in req.messages if m.role == "user"])
    if len(user_content) > settings.max_message_chars:
        raise HTTPException(status_code=400, detail="Input exceeds max_message_chars")

    sanitization = sanitize_text(user_content)
    if sanitization.flagged_patterns:
        logger.info("Prompt injection signals detected: %s", sanitization.flagged_patterns)

    safety_classifier = get_safety_classifier()
    pre_safety = safety_classifier.predict(sanitization.text)

    provider = get_provider()
    if pre_safety.label == "harmful" and pre_safety.score >= settings.safety_harm_threshold:
        draft = "Generation blocked by safety pre-check."
        post_safety = pre_safety
    else:
        try:
            draft = await provider.generate(
                prompt=sanitization.text,
                temperature=req.temperature,
                seed=req.seed,
            )
        except Exception as exc:
            logger.exception("LLM provider error: %s", exc)
            raise HTTPException(status_code=500, detail="LLM provider request failed") from exc
        post_safety = safety_classifier.predict(draft)

    engine = ConstitutionEngine()
    violations, rule_log, final_answer = engine.evaluate(
        RuleContext(
            user_text=sanitization.text,
            draft=draft,
            sanitizer_flags=sanitization.flagged_patterns,
            pre_safety_label=pre_safety.label,
            pre_safety_score=pre_safety.score,
            post_safety_label=post_safety.label,
            post_safety_score=post_safety.score,
            safety_threshold=settings.safety_harm_threshold,
        )
    )

    return ChatResponse(
        draft=draft,
        violations=violations,
        final_answer=final_answer,
        confidence=confidence_from_violations(violations),
        rule_applied_log=rule_log,
    )
