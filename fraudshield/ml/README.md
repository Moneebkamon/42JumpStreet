# ml/: the ready phishing-URL model and how we check it

The app can use `CrabInHoney/urlbert-tiny-v2-phishing-classifier` (MIT, 3.7M parameters) as one extra scoring signal.
It is **optional**: without the files the app behaves exactly as before (`ml_available: 0`).

## Get the model (15 MB, safetensors only, no code is run when loading)
Download these files from `https://huggingface.co/CrabInHoney/urlbert-tiny-v2-phishing-classifier/resolve/main/<file>`
into `ml/artifacts/urlbert-tiny-v2/`: `config.json`, `model.safetensors`, `special_tokens_map.json`, `tokenizer.json`,
`tokenizer_config.json`, `vocab.txt`, `README.md`. Check that `model.safetensors` has SHA-256
`ad9130a5b6f8b2ace28bf0e61826fec7b6cb0cf500a081ff6891f78fd408f5ab`. `ml/artifacts/` is git-ignored.
The backend needs `numpy`, `safetensors`, `tokenizers` (in `backend/requirements.txt`). Set `FRAUDSHIELD_ML=0` to turn it off.

## What is where
| File | Job | Venv |
|---|---|---|
| `backend/app/ml/` | runs the model in plain numpy inside the app | backend |
| `ml/tiny_bert.py` | the same model in torch, used only as the reference and for evaluation | ml |
| `ml/build_eval_set.py` -> `score_with_model.py` -> `report.py` | held-out comparison (see `docs/ready-model-eval.md`) | backend, ml, any |
| `backend/tests/fixtures/urlbert_reference.json` | torch probabilities the numpy version must match (test) | |

`ml/.venv` holds `torch` (CPU) for the reference only. The app never needs it.

## Notes
- The model must see the URL **without** `https://`. The app does this in `app/ml/predictor.py`.
- `transformers` cannot be used on this machine: its `regex` dependency is blocked by Windows Application Control.
- The model's `tokenizer.json` pads to 64 tokens by default; the app turns padding off (it has no attention mask).
- Do not test on `ealvaradob/phishing-dataset` (the model was trained on it).
