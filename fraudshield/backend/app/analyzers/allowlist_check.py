"""Is this domain on the admin-reviewed allowlist? Key: allowlisted. A missing or unreadable store means "no"."""
from app.analyzers.url_analyzer.normalizer import NormalizedURL
from app.repositories import allowlist_repo


def allowlist_features(n: NormalizedURL) -> dict:
    try:
        return {"allowlisted": int(allowlist_repo.is_allowlisted(n.host))}
    except Exception:
        return {"allowlisted": 0}
