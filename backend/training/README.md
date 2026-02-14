# Safety Classifier Training

## Recommended datasets

- `allenai/wildguardmix`
- `Anthropic/hh-rlhf`
- `PKU-Alignment/BeaverTails`

Use `training/download_datasets.py` to normalize rows to:

```json
{"text": "...", "label": "safe|harmful"}
```

## Commands

```bash
cd backend
python -m training.download_datasets --dataset allenai/wildguardmix --split train --out training/data/raw_dataset.jsonl
python -m training.train_safety_classifier --train-files training/data/raw_dataset.jsonl training/data/local_hard_negatives.jsonl --out-model models/safety_classifier.joblib
python -m training.evaluate_classifier --suite evals/suites/core_redteam.json
```

## Notes

- Add your own failure prompts to `training/data/local_hard_negatives.jsonl`.
- Retrain whenever safety misses appear in manual testing.
- Keep `SAFETY_CLASSIFIER_MODE=trained` in `.env` after model artifact exists.
