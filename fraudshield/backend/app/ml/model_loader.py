"""Find and load the ready phishing-URL model (a tiny BERT, safetensors weights, MIT licence).

Optional by design: if the model files or the small numeric packages are missing, or FRAUDSHIELD_ML=0, loading returns
None and the rest of the app works exactly as before. Weights are plain tensors (safetensors), never pickles.
Get the files with: see ml/README.md. Default location: ml/artifacts/urlbert-tiny-v2 at the repo root.
"""
import json
import os
from functools import lru_cache
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parents[3] / "ml" / "artifacts" / "urlbert-tiny-v2"
_REQUIRED = ("config.json", "model.safetensors", "tokenizer.json")


def model_dir() -> Path:
    return Path(os.environ.get("FRAUDSHIELD_MODEL_DIR", DEFAULT_DIR))


@lru_cache(maxsize=4)
def _load(directory: str) -> dict | None:
    d = Path(directory)
    if not all((d / f).exists() for f in _REQUIRED):
        return None
    try:
        from safetensors.numpy import load_file
        from tokenizers import Tokenizer

        cfg = json.loads((d / "config.json").read_text(encoding="utf-8"))
        tok = Tokenizer.from_file(str(d / "tokenizer.json"))
        tok.enable_truncation(max_length=cfg["max_position_embeddings"])
        tok.no_padding()  # tokenizer.json ships fixed padding to 64; padded tokens would be attended to (no mask here)
        return {"cfg": cfg, "w": load_file(d / "model.safetensors"), "tok": tok}
    except Exception:  # missing package, corrupt file...: the model is a bonus, never a requirement
        return None


def load_model() -> dict | None:
    """The loaded model bundle, or None when disabled or unavailable."""
    if os.environ.get("FRAUDSHIELD_ML", "1") == "0":
        return None
    return _load(str(model_dir()))
