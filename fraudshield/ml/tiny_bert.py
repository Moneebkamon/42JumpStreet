"""A minimal BERT sequence classifier in plain torch, for the ready model in ml/artifacts/urlbert-tiny-v2.

Why this exists: the `transformers` package needs the `regex` package, whose compiled file is blocked by this machine's
Windows Application Control policy. `torch`, `safetensors` and `tokenizers` load fine, and the weights follow the standard
BERT layout, so we run the model directly. Inference only. The architecture values come from the model's config.json.
"""
import json
import math
from pathlib import Path

import torch
import torch.nn.functional as F
from safetensors.torch import load_file
from tokenizers import Tokenizer


class TinyBertClassifier:
    def __init__(self, model_dir: Path | str):
        d = Path(model_dir)
        self.cfg = json.loads((d / "config.json").read_text(encoding="utf-8"))
        self.w = load_file(d / "model.safetensors")  # safetensors: plain tensors, cannot run code when loaded
        self.tok = Tokenizer.from_file(str(d / "tokenizer.json"))
        self.max_len = self.cfg["max_position_embeddings"]
        self.tok.enable_truncation(max_length=self.max_len)
        self.tok.enable_padding(pad_id=self.cfg["pad_token_id"], pad_token="[PAD]")
        self.phish_index = int(self.cfg["label2id"]["phish"])

    def _ln(self, x, prefix):
        return F.layer_norm(x, (x.shape[-1],), self.w[f"{prefix}.weight"], self.w[f"{prefix}.bias"],
                            self.cfg["layer_norm_eps"])

    def _lin(self, x, prefix):
        return F.linear(x, self.w[f"{prefix}.weight"], self.w[f"{prefix}.bias"])

    @torch.no_grad()
    def _forward(self, ids: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        c, w = self.cfg, self.w
        heads, hidden = c["num_attention_heads"], c["hidden_size"]
        dh = hidden // heads
        b, t = ids.shape

        x = w["bert.embeddings.word_embeddings.weight"][ids]
        x = x + w["bert.embeddings.position_embeddings.weight"][torch.arange(t)][None]
        x = x + w["bert.embeddings.token_type_embeddings.weight"][0][None, None]  # single segment
        x = self._ln(x, "bert.embeddings.LayerNorm")

        bias = (1.0 - mask[:, None, None, :].float()) * -1e9  # hide padding from attention
        for i in range(c["num_hidden_layers"]):
            p = f"bert.encoder.layer.{i}"
            q, k, v = (self._lin(x, f"{p}.attention.self.{n}").view(b, t, heads, dh).transpose(1, 2)
                       for n in ("query", "key", "value"))
            att = torch.softmax(q @ k.transpose(-1, -2) / math.sqrt(dh) + bias, dim=-1)
            ctx = (att @ v).transpose(1, 2).reshape(b, t, hidden)
            x = self._ln(self._lin(ctx, f"{p}.attention.output.dense") + x, f"{p}.attention.output.LayerNorm")
            h = F.gelu(self._lin(x, f"{p}.intermediate.dense"))
            x = self._ln(self._lin(h, f"{p}.output.dense") + x, f"{p}.output.LayerNorm")

        pooled = torch.tanh(self._lin(x[:, 0], "bert.pooler.dense"))
        return self._lin(pooled, "classifier")

    def phish_probability(self, texts: list[str], batch: int = 64) -> list[float]:
        out: list[float] = []
        for i in range(0, len(texts), batch):
            enc = self.tok.encode_batch(texts[i:i + batch])
            ids = torch.tensor([e.ids for e in enc])
            mask = torch.tensor([e.attention_mask for e in enc])
            out.extend(torch.softmax(self._forward(ids, mask), dim=-1)[:, self.phish_index].tolist())
        return out
