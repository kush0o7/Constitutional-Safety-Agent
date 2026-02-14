from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    seed: int | None = Field(default=None)

    @field_validator("messages")
    @classmethod
    def must_include_user_message(cls, messages: list[Message]) -> list[Message]:
        if not any(m.role == "user" for m in messages):
            raise ValueError("At least one user message is required")
        return messages


class RuleViolation(BaseModel):
    rule: str
    violated: bool
    reason: str


class RuleLogEntry(BaseModel):
    rule: str
    status: Literal["applied", "violated", "not_triggered"]
    detail: str


class ChatResponse(BaseModel):
    draft: str
    violations: list[RuleViolation]
    final_answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    rule_applied_log: list[RuleLogEntry]


class EvalSummary(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float
    failed_ids: list[str]
    violations_by_rule: dict[str, int]


class EvalResult(BaseModel):
    id: str
    expected_outcome: str
    actual_outcome: str
    expected_violated_rules: list[str]
    actual_violated_rules: list[str]
    passed: bool
    confidence: float
    final_answer: str


class LatestEvalReportResponse(BaseModel):
    generated_at: str
    summary: EvalSummary
    results: list[EvalResult]
    source_file: str
