from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def load_jsonl(path: Path) -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            text = str(obj.get("text", "")).strip()
            label = str(obj.get("label", "")).strip().lower()
            if not text or label not in {"safe", "harmful"}:
                continue
            texts.append(text)
            labels.append(label)

    return texts, labels


def main() -> None:
    parser = argparse.ArgumentParser(description="Train safety classifier from JSONL files")
    parser.add_argument(
        "--train-files",
        nargs="+",
        default=["training/data/raw_dataset.jsonl", "training/data/local_hard_negatives.jsonl"],
        help="Input JSONL files with {text,label}",
    )
    parser.add_argument(
        "--out-model",
        default="models/safety_classifier.joblib",
        help="Output model artifact path",
    )
    args = parser.parse_args()

    all_texts: list[str] = []
    all_labels: list[str] = []

    for file_path in args.train_files:
        path = Path(file_path)
        if not path.exists():
            print(f"Skipping missing file: {path}")
            continue
        texts, labels = load_jsonl(path)
        all_texts.extend(texts)
        all_labels.extend(labels)
        print(f"Loaded {len(texts)} rows from {path}")

    if len(all_texts) < 50:
        raise RuntimeError("Not enough training data. Download at least one dataset first.")

    x_train, x_test, y_train, y_test = train_test_split(
        all_texts,
        all_labels,
        test_size=0.2,
        random_state=42,
        stratify=all_labels,
    )

    model = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=120000,
                    strip_accents="unicode",
                ),
            ),
            ("clf", LogisticRegression(max_iter=300, class_weight="balanced")),
        ]
    )
    model.fit(x_train, y_train)

    preds = model.predict(x_test)
    report = classification_report(y_test, preds, digits=4)
    print("\nValidation report:\n")
    print(report)

    out_path = Path(args.out_model)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out_path)
    print(f"Saved model: {out_path}")


if __name__ == "__main__":
    main()
