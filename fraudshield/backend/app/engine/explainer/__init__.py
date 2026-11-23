"""Plain-language explanation of a scan result.

Always produced by fixed templates from the findings that actually fired (no LLM, no invented facts). `llm_client.py` is a
reserved slot for an optional, clearly-labelled rewrite later; it is not built and nothing depends on it.
"""
from app.engine.explainer.evidence_selector import select
from app.engine.explainer.fallback_templates import write


def explain(result: dict) -> str:
    return write(result, select(result))
