from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets import load_dataset


def _pick_text(example: dict) -> str | None:
    for key in ("prompt", "text", "instruction", "user_input", "question", "query"):
        value = example.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    # Common chat/message format fallback
    messages = example.get("messages")
    if isinstance(messages, list):
        parts: list[str] = []
        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get("content")
                role = msg.get("role")
                if role in {"user", "human"} and isinstance(content, str):
                    parts.append(content)
        if parts:
            return "\n".join(parts)
    return None


def _pick_label(example: dict) -> str | None:
    # Map many possible label layouts to safe/harmful
    for key in (
        "label",
        "harmful",
        "is_harmful",
        "prompt_harmfulness",
        "safety_label",
        "category",
    ):
        if key not in example:
            continue
        value = example[key]

        if isinstance(value, bool):
            return "harmful" if value else "safe"

        if isinstance(value, (int, float)):
            return "harmful" if value > 0 else "safe"

        if isinstance(value, str):
            lower = value.lower().strip()
            if any(tok in lower for tok in ("harm", "unsafe", "attack", "jailbreak", "toxic", "illegal")):
                return "harmful"
            if any(tok in lower for tok in ("safe", "benign", "helpful", "harmless")):
                return "safe"

    return None


def _extract_pairwise_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def export_dataset(
    dataset_id: str,
    split: str,
    out_path: Path,
    max_rows: int,
    pairwise_mode: str,
) -> int:
    ds = load_dataset(dataset_id, split=split)

    written = 0
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for row in ds:
            if pairwise_mode == "hh_rlhf":
                chosen = _extract_pairwise_text(row.get("chosen"))
                rejected = _extract_pairwise_text(row.get("rejected"))

                if chosen:
                    f.write(json.dumps({"text": chosen, "label": "safe"}) + "\n")
                    written += 1
                if rejected:
                    f.write(json.dumps({"text": rejected, "label": "harmful"}) + "\n")
                    written += 1
                if max_rows > 0 and written >= max_rows:
                    break
                continue

            text = _pick_text(row)
            label = _pick_label(row)
            if not text or label not in {"safe", "harmful"}:
                continue

            f.write(json.dumps({"text": text, "label": label}) + "\n")
            written += 1
            if max_rows > 0 and written >= max_rows:
                break

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and normalize safety datasets to JSONL")
    parser.add_argument("--dataset", required=True, help="HF dataset id, e.g. allenai/wildguardmix")
    parser.add_argument("--split", default="train", help="dataset split")
    parser.add_argument("--out", default="training/data/raw_dataset.jsonl", help="output jsonl path")
    parser.add_argument("--max-rows", type=int, default=30000, help="max rows to export (0 = all)")
    parser.add_argument(
        "--pairwise-mode",
        default="none",
        choices=["none", "hh_rlhf"],
        help="Special handling for pairwise preference datasets.",
    )
    args = parser.parse_args()

    count = export_dataset(args.dataset, args.split, Path(args.out), args.max_rows, args.pairwise_mode)
    print(f"Wrote {count} rows to {args.out}")


if __name__ == "__main__":
    main()
