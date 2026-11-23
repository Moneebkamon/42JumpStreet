"""Hard overrides applied after scoring: official domains are capped low, threat-feed hits floored high."""

OFFICIAL_CAP = 10
ALLOWLIST_CAP = 10  # a reviewed false positive; a threat-feed hit still wins over it (applied after)
THREAT_FEED_FLOOR = 85


def apply_overrides(score: int, features: dict) -> tuple[int, list[str]]:
    notes: list[str] = []
    if features.get("brand_is_official") == 1:
        score = min(score, OFFICIAL_CAP)
        notes.append(f"Domain is an official domain of {features.get('brand_name') or 'a protected brand'}")
    if features.get("allowlisted") == 1:
        score = min(score, ALLOWLIST_CAP)
        notes.append("Domain was reviewed by an administrator and allowlisted as a false positive")
    if features.get("threat_listed") == 1:
        score = max(score, THREAT_FEED_FLOOR)
        notes.append("Domain is listed in a known threat feed")
    return score, notes
