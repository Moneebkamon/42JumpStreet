"""Create a scan result and store it so it can be fetched later (GET /scan/{id}, history)."""
import logging
import os
import uuid

from app.analyzers.url_analyzer.normalizer import normalize
from app.discovery import domain_watch
from app.engine.explainer import explain
from app.engine.pipeline import run_pipeline
from app.repositories import allowlist_repo, scan_repo

log = logging.getLogger(__name__)


def _network_enabled() -> bool:
    """Network lookups (RDAP/DNS/TLS) are on unless FRAUDSHIELD_NETWORK=0 (used by tests)."""
    return os.environ.get("FRAUDSHIELD_NETWORK", "1") != "0"


def _prewarmed(raw_url: str) -> dict | None:
    """A result discovery already computed, for a plain domain link (no path/query). Else None."""
    try:
        n = normalize(raw_url)
    except ValueError:
        return None
    if n.path != "/" or n.query:
        return None
    if allowlist_repo.is_allowlisted(n.host):
        return None  # an allowlisted domain is re-scored so the override applies
    return domain_watch.cached_result(n.host)


def _store(response: dict, deep: bool) -> None:
    """Persist the scan. A storage problem must never break the scan itself."""
    try:
        scan_repo.save(response, host=normalize(response["url"]).host, deep=deep)
    except Exception:
        log.exception("could not store scan %s", response.get("scan_id"))


def scan_url(raw_url: str, deep: bool = False) -> dict:
    """Raises ValueError if the URL is unusable. deep=True also opens the page in the sandbox."""
    if not deep and (hit := _prewarmed(raw_url)):
        response = {**hit, "scan_id": uuid.uuid4().hex, "state": "complete", "cached": True}
        response["explanation"] = response.get("explanation") or explain(response)
    else:
        result = run_pipeline(raw_url, use_network=_network_enabled(), deep=deep)
        response = {"scan_id": uuid.uuid4().hex, "state": "complete", **result}
    _store(response, deep)
    return response
