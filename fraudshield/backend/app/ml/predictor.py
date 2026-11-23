"""Run the ready phishing-URL model in plain numpy (no torch needed in the app). Keys start with ml_.

The model reads URL text WITHOUT the scheme ("https://" makes it flag almost everything; see docs/ready-model-eval.md).
It is global (not UAE-specific) and biased by domain ending, so its output is one weak signal, never a verdict.
Parity with the torch reference is checked in tests/unit/test_ml_model.py.
"""
import math

import numpy as np

from app.analyzers.url_analyzer.normalizer import NormalizedURL
from app.ml.model_loader import load_model


def _erf(x: np.ndarray) -> np.ndarray:
    """Abramowitz-Stegun 7.1.26 (max error ~1.5e-7); numpy has no erf and scipy is not a dependency."""
    s = np.sign(x)
    a = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * a)
    poly = ((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592
    return s * (1.0 - poly * t * np.exp(-a * a))


def _gelu(x: np.ndarray) -> np.ndarray:
    return 0.5 * x * (1.0 + _erf(x / math.sqrt(2.0)))


def _layer_norm(x: np.ndarray, w: np.ndarray, b: np.ndarray, eps: float) -> np.ndarray:
    mean = x.mean(-1, keepdims=True)
    var = ((x - mean) ** 2).mean(-1, keepdims=True)
    return (x - mean) / np.sqrt(var + eps) * w + b


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max(-1, keepdims=True))
    return e / e.sum(-1, keepdims=True)


def _logits(model: dict, ids: list[int]) -> np.ndarray:
    c, w = model["cfg"], model["w"]
    heads, hidden, eps = c["num_attention_heads"], c["hidden_size"], c["layer_norm_eps"]
    dh = hidden // heads
    t = len(ids)

    def lin(x, p):
        return x @ w[f"{p}.weight"].T + w[f"{p}.bias"]

    x = w["bert.embeddings.word_embeddings.weight"][ids] + w["bert.embeddings.position_embeddings.weight"][:t]
    x = x + w["bert.embeddings.token_type_embeddings.weight"][0]
    x = _layer_norm(x, w["bert.embeddings.LayerNorm.weight"], w["bert.embeddings.LayerNorm.bias"], eps)

    for i in range(c["num_hidden_layers"]):
        p = f"bert.encoder.layer.{i}"
        q, k, v = (lin(x, f"{p}.attention.self.{n}").reshape(t, heads, dh).transpose(1, 0, 2)
                   for n in ("query", "key", "value"))
        att = _softmax(q @ k.transpose(0, 2, 1) / math.sqrt(dh))
        ctx = (att @ v).transpose(1, 0, 2).reshape(t, hidden)
        x = _layer_norm(lin(ctx, f"{p}.attention.output.dense") + x,
                        w[f"{p}.attention.output.LayerNorm.weight"], w[f"{p}.attention.output.LayerNorm.bias"], eps)
        h = _gelu(lin(x, f"{p}.intermediate.dense"))
        x = _layer_norm(lin(h, f"{p}.output.dense") + x,
                        w[f"{p}.output.LayerNorm.weight"], w[f"{p}.output.LayerNorm.bias"], eps)

    pooled = np.tanh(lin(x[0], "bert.pooler.dense"))
    return lin(pooled, "classifier")


def phish_probability(text: str) -> float | None:
    """Probability (0..1) that the URL text looks like phishing, or None when the model is unavailable."""
    model = load_model()
    if model is None:
        return None
    ids = model["tok"].encode(text).ids
    phish = int(model["cfg"]["label2id"]["phish"])
    return float(_softmax(_logits(model, ids))[phish])


def model_input(n: NormalizedURL) -> str:
    """What the model is shown: the normalized URL without its scheme, e.g. 'example.com/login'."""
    return n.url.split("://", 1)[-1]


def ml_features(n: NormalizedURL) -> dict:
    p = phish_probability(model_input(n))
    if p is None:
        return {"ml_available": 0}
    return {"ml_available": 1, "ml_phish_prob": round(p, 4)}
