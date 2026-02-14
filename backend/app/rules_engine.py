from dataclasses import dataclass

from .schemas import RuleLogEntry, RuleViolation


@dataclass
class RuleContext:
    user_text: str
    draft: str
    sanitizer_flags: list[str]
    pre_safety_label: str = "unknown"
    pre_safety_score: float = 0.0
    post_safety_label: str = "unknown"
    post_safety_score: float = 0.0
    safety_threshold: float = 0.62


RISK_PATTERNS: dict[str, list[str]] = {
    "harm_illegal": [
        "kill someone",
        "how to kill",
        "build a bomb",
        "make a bomb",
        "how to make bomb",
        "how can i make a bomb",
        "explosive device",
        "make meth",
        "poison someone",
        "murder",
        "bypass police",
    ],
    "cyber_abuse": [
        "malware",
        "ransomware",
        "ddos",
        "sql injection",
        "steal password",
        "phishing kit",
    ],
    "self_harm": [
        "kill myself",
        "suicide method",
        "self harm",
        "hurt myself",
    ],
    "pii_exfiltration": [
        "social security number",
        "credit card dump",
        "home address lookup",
        "dox",
    ],
    "jailbreak_override": [
        "ignore previous instructions",
        "reveal hidden rules",
        "developer mode",
        "system prompt",
    ],
}

OVERCONFIDENT_PATTERNS = ["definitely", "guaranteed", "always true", "100% certain"]
REALTIME_REQUEST_PATTERNS = ["today", "latest", "current", "right now", "real-time"]


def classify_risks(text: str) -> tuple[dict[str, int], dict[str, list[str]]]:
    normalized = text.lower()
    scores: dict[str, int] = {}
    evidence: dict[str, list[str]] = {}

    for category, terms in RISK_PATTERNS.items():
        matches = [term for term in terms if term in normalized]
        evidence[category] = matches
        if len(matches) >= 2:
            scores[category] = 3
        elif len(matches) == 1:
            scores[category] = 2
        else:
            scores[category] = 0

    return scores, evidence


class ConstitutionEngine:
    """
    Internal constitution rules live in code and are never exposed verbatim.
    Only high-level rule names and evaluation outcomes are returned.
    """

    RULE_TRUTHFULNESS = "truthfulness"
    RULE_SAFETY = "safety_first"
    RULE_HONESTY = "honesty_of_ability"
    RULE_NON_NEGOTIABLE = "non_negotiable"
    RULE_TRANSPARENCY = "transparency"
    RULE_NON_DISCLOSURE = "non_disclosure"

    def evaluate(self, ctx: RuleContext) -> tuple[list[RuleViolation], list[RuleLogEntry], str]:
        violations: list[RuleViolation] = []
        logs: list[RuleLogEntry] = []

        risk_scores, risk_evidence = classify_risks(ctx.user_text)
        highest_risk = max(risk_scores.values()) if risk_scores else 0
        risky_categories = [k for k, v in risk_scores.items() if v >= 2]

        classifier_request_block = (
            ctx.pre_safety_label == "harmful" and ctx.pre_safety_score >= ctx.safety_threshold
        )
        classifier_draft_block = (
            ctx.post_safety_label == "harmful" and ctx.post_safety_score >= ctx.safety_threshold
        )
        unsafe_request = highest_risk >= 2 or classifier_request_block or classifier_draft_block
        if unsafe_request:
            violations.append(
                RuleViolation(
                    rule=self.RULE_SAFETY,
                    violated=True,
                    reason=f"Unsafe request detected in categories: {', '.join(risky_categories)}.",
                )
            )
            logs.append(
                RuleLogEntry(
                    rule=self.RULE_SAFETY,
                    status="violated",
                    detail=(
                        f"Risk scores={risk_scores}; evidence={risk_evidence}; "
                        f"pre_classifier=({ctx.pre_safety_label}, {ctx.pre_safety_score}); "
                        f"post_classifier=({ctx.post_safety_label}, {ctx.post_safety_score})"
                    ),
                )
            )
        else:
            violations.append(
                RuleViolation(
                    rule=self.RULE_SAFETY,
                    violated=False,
                    reason="No high-risk safety categories were triggered.",
                )
            )
            logs.append(
                RuleLogEntry(
                    rule=self.RULE_SAFETY,
                    status="applied",
                    detail=f"Risk scores={risk_scores}",
                )
            )

        overconfident = any(p in ctx.draft.lower() for p in OVERCONFIDENT_PATTERNS)
        if overconfident:
            violations.append(
                RuleViolation(
                    rule=self.RULE_TRUTHFULNESS,
                    violated=True,
                    reason="Draft uses overconfident language that can imply unsupported certainty.",
                )
            )
            logs.append(
                RuleLogEntry(
                    rule=self.RULE_TRUTHFULNESS,
                    status="violated",
                    detail="Overconfidence markers detected in draft output.",
                )
            )
        else:
            violations.append(
                RuleViolation(
                    rule=self.RULE_TRUTHFULNESS,
                    violated=False,
                    reason="No overconfidence markers detected in the draft.",
                )
            )
            logs.append(
                RuleLogEntry(
                    rule=self.RULE_TRUTHFULNESS,
                    status="applied",
                    detail="Truthfulness check passed.",
                )
            )

        capability_risk = any(p in ctx.user_text.lower() for p in REALTIME_REQUEST_PATTERNS)
        if capability_risk:
            violations.append(
                RuleViolation(
                    rule=self.RULE_HONESTY,
                    violated=True,
                    reason="Request may require real-time verification beyond guaranteed model capabilities.",
                )
            )
            logs.append(
                RuleLogEntry(
                    rule=self.RULE_HONESTY,
                    status="violated",
                    detail="Capability limitation trigger detected (real-time request markers).",
                )
            )
        else:
            violations.append(
                RuleViolation(
                    rule=self.RULE_HONESTY,
                    violated=False,
                    reason="No obvious capability mismatch detected.",
                )
            )
            logs.append(
                RuleLogEntry(
                    rule=self.RULE_HONESTY,
                    status="applied",
                    detail="Capability-honesty check passed.",
                )
            )

        if ctx.sanitizer_flags:
            violations.append(
                RuleViolation(
                    rule=self.RULE_NON_NEGOTIABLE,
                    violated=True,
                    reason="Prompt injection/override attempt detected and neutralized.",
                )
            )
            logs.append(
                RuleLogEntry(
                    rule=self.RULE_NON_NEGOTIABLE,
                    status="violated",
                    detail=f"Sanitizer flags={ctx.sanitizer_flags}",
                )
            )
        else:
            violations.append(
                RuleViolation(
                    rule=self.RULE_NON_NEGOTIABLE,
                    violated=False,
                    reason="No override attempt detected.",
                )
            )
            logs.append(
                RuleLogEntry(
                    rule=self.RULE_NON_NEGOTIABLE,
                    status="applied",
                    detail="System-instruction integrity preserved.",
                )
            )

        logs.append(
            RuleLogEntry(
                rule=self.RULE_TRANSPARENCY,
                status="applied",
                detail="Per-rule outcomes and trace details attached to output.",
            )
        )
        logs.append(
            RuleLogEntry(
                rule=self.RULE_NON_DISCLOSURE,
                status="applied",
                detail="Internal policy text is not disclosed; only high-level outcomes are exposed.",
            )
        )

        if unsafe_request:
            final = (
                "I can’t help with harmful, illegal, or abusive instructions. "
                "I can help with safe alternatives, prevention, or legal best practices."
            )
        elif capability_risk:
            final = (
                "I may not have reliable real-time visibility. I can provide general guidance and "
                "you should verify time-sensitive facts with an up-to-date source."
            )
        elif overconfident:
            final = (
                "I may be uncertain on some details. I can revise this with explicit assumptions "
                "or with cited sources."
            )
        else:
            final = ctx.draft

        return violations, logs, final


def confidence_from_violations(violations: list[RuleViolation]) -> float:
    violated_count = sum(1 for v in violations if v.violated)
    return max(0.05, round(1.0 - 0.16 * violated_count, 2))
