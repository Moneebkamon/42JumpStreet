"""Which discovered domains deserve a deeper look first, under a time budget? Pure maths; it never fetches anything.

This only RECOMMENDS. Opening a suspected scam site is a separate step that needs a human's explicit approval.

value of a domain = harm weight x suspicion x informativeness
- suspicion:        score / 100 (a likelier scam is worth more)
- informativeness:  1 at score 50, falling to 0.25 at 0 or 100. Scores near the middle are where the cheap URL-only
                    check is least sure, so a closer look changes the answer most. (Active-learning idea.)
- harm weight:      banks, government and telcos hurt victims more than a parcel brand; unknown brand = 1.0

Selection: greedy by value per second of scan cost, until the budget is used. With equal costs (the default) this is
exactly "take the top k", which is the optimal answer to that knapsack. All weights are hand-set starting values.
"""
from app.analyzers.brand_detector.registry import get_brands

DEFAULT_COST_SECONDS = 5.0  # measured ~4-5 s per deep scan (see CURRENT_STAGE.md)
HARM_BY_CATEGORY = {"bank": 1.5, "government": 1.5, "telecom": 1.3, "payment": 1.3}


def harm_weight(brand_id: str) -> float:
    for b in get_brands():
        if b.id == brand_id:
            return HARM_BY_CATEGORY.get(b.category, 1.0)
    return 1.0


def value(detection: dict) -> float:
    p = detection["score"] / 100
    informativeness = 0.25 + 0.75 * (1 - abs(2 * p - 1))
    return round(harm_weight(detection.get("brand_id", "")) * p * informativeness, 4)


def prioritize(
    detections: list[dict], budget_seconds: float, cost_seconds: float = DEFAULT_COST_SECONDS
) -> list[dict]:
    """Return the chosen detections, best first, each with `priority` and `est_cost_s`. Total cost <= budget."""
    if budget_seconds <= 0 or cost_seconds <= 0:
        return []
    ranked = sorted(
        ({**d, "priority": value(d), "est_cost_s": cost_seconds} for d in detections if d["score"] > 0),
        key=lambda d: (-d["priority"] / d["est_cost_s"], d["domain"]),
    )
    chosen, spent = [], 0.0
    for d in ranked:
        if spent + d["est_cost_s"] <= budget_seconds:
            chosen.append(d)
            spent += d["est_cost_s"]
    return chosen
