"""Merge rule points and (optionally) an ML score into one 0-100 score."""

RULE_SHARE = 0.6  # weight of rules when an ML score exists


def combine(rule_points: int, ml_score: float | None = None) -> int:
    capped = min(100, max(0, rule_points))
    if ml_score is None:
        return capped
    ml = min(100.0, max(0.0, ml_score))
    return round(RULE_SHARE * capped + (1 - RULE_SHARE) * ml)
