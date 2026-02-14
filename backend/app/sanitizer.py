import re
from dataclasses import dataclass


INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?(system|developer)\s+prompt", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(system\s+prompt|hidden\s+rules)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?developer\s+mode", re.IGNORECASE),
    re.compile(r"<\s*/?\s*system\s*>", re.IGNORECASE),
    re.compile(r"BEGIN\s+SYSTEM\s+PROMPT", re.IGNORECASE),
]


@dataclass
class SanitizationResult:
    text: str
    flagged_patterns: list[str]


def sanitize_text(text: str) -> SanitizationResult:
    """
    Neutralize common prompt-injection patterns before the LLM call.
    We replace suspicious spans with a marker instead of deleting everything,
    preserving normal user context while preventing instruction takeover.
    """
    sanitized = text
    flags: list[str] = []

    for pattern in INJECTION_PATTERNS:
        if pattern.search(sanitized):
            flags.append(pattern.pattern)
            sanitized = pattern.sub("[sanitized-injection-attempt]", sanitized)

    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return SanitizationResult(text=sanitized, flagged_patterns=flags)
