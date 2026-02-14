from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.safety_classifier import get_safety_classifier


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate safety classifier on eval suite prompts")
    parser.add_argument("--suite", default="evals/suites/core_redteam.json")
    args = parser.parse_args()

    suite = json.loads(Path(args.suite).read_text())
    clf = get_safety_classifier()

    total = 0
    correct = 0
    for case in suite:
        prompt = case["prompt"]
        expected = "harmful" if case["expected_outcome"] == "refuse" else "safe"
        pred = clf.predict(prompt)
        is_correct = pred.label == expected
        total += 1
        correct += int(is_correct)
        print(
            f"{case['id']}: expected={expected} predicted={pred.label} "
            f"score={pred.score} source={pred.source} {'OK' if is_correct else 'MISS'}"
        )

    accuracy = (correct / total) * 100 if total else 0.0
    print(f"\nAccuracy: {accuracy:.2f}% ({correct}/{total})")


if __name__ == "__main__":
    main()
