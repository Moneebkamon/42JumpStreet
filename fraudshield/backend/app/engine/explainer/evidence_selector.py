"""Pick the few findings that matter most for an explanation (3-5), highest impact first.

Overrides (official domain, threat-feed hit) come first because they change the verdict outright. Then fired rules by points.
"""

MAX_FINDINGS = 4


def select(result: dict, limit: int = MAX_FINDINGS) -> list[dict]:
    reasons = result.get("reasons") or []
    overrides = [r for r in reasons if r.get("rule") == "override"]
    rules = sorted((r for r in reasons if r.get("rule") != "override" and r.get("points", 0) > 0),
                   key=lambda r: r["points"], reverse=True)
    return (overrides + rules)[:limit]
