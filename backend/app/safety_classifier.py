from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .config import settings


@dataclass
class SafetyPrediction:
    label: str
    score: float
    source: str


class SafetyClassifier(Protocol):
    def predict(self, text: str) -> SafetyPrediction:
        ...


class HeuristicSafetyClassifier:
    HARMFUL_TERMS = [
        "kill someone",
        "how to kill",
        "murder",
        "make a bomb",
        "build a bomb",
        "explosive device",
        "make meth",
        "cocaine",
        "heroin",
        "steal password",
        "malware",
        "ransomware",
        "ddos",
        "phishing",
    ]

    def predict(self, text: str) -> SafetyPrediction:
        lower = text.lower()
        hits = [term for term in self.HARMFUL_TERMS if term in lower]
        if hits:
            score = min(0.99, 0.55 + 0.12 * len(hits))
            return SafetyPrediction(label="harmful", score=round(score, 3), source="heuristic")
        return SafetyPrediction(label="safe", score=0.9, source="heuristic")


class SklearnSafetyClassifier:
    def __init__(self, model_path: str) -> None:
        import joblib

        self.model = joblib.load(model_path)

    def predict(self, text: str) -> SafetyPrediction:
        labels = self.model.predict([text])
        label = str(labels[0])

        score = 0.5
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba([text])[0]
            classes = list(getattr(self.model, "classes_", []))
            if label in classes:
                score = float(probs[classes.index(label)])
            else:
                score = float(max(probs))

        return SafetyPrediction(label=label, score=round(score, 3), source="sklearn")


_cached_classifier: SafetyClassifier | None = None


def get_safety_classifier() -> SafetyClassifier:
    global _cached_classifier
    if _cached_classifier is not None:
        return _cached_classifier

    if settings.safety_classifier_mode == "trained":
        model_path = Path(settings.safety_model_path)
        if not model_path.is_absolute():
            model_path = Path(__file__).resolve().parents[1] / model_path

        if model_path.exists():
            _cached_classifier = SklearnSafetyClassifier(str(model_path))
            return _cached_classifier

    _cached_classifier = HeuristicSafetyClassifier()
    return _cached_classifier
