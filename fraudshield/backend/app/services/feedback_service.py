"""Review "this is safe" reports on links we flagged, and promote confirmed false positives to the allowlist.

Guard rails: shared-hosting domains (github.io, blogspot.com, ...) can never be allowlisted, because one good page there says
nothing about the other sites on the platform; a domain that is in a threat feed cannot be allowlisted either; and the
allowlist only lowers a score, it never beats a threat-feed hit.
"""
from app.analyzers.threat_intel.feed_lookup import is_shared_hosting, threat_features
from app.analyzers.url_analyzer.normalizer import normalize
from app.core.errors import Conflict, NotFound
from app.repositories import allowlist_repo, scan_repo
from app.services import audit_service


def queue(limit: int = 100) -> list[dict]:
    done = allowlist_repo.reviewed_ids()
    out = []
    for s in scan_repo.flagged_but_marked_safe(limit * 2):
        if s["scan_id"] in done:
            continue
        out.append({**s, "already_allowlisted": allowlist_repo.is_allowlisted(s["host"]),
                    "shared_hosting": is_shared_hosting(s["host"])})
        if len(out) >= limit:
            break
    return out


def _scan(scan_id: str) -> dict:
    s = scan_repo.get(scan_id)
    if s is None:
        raise NotFound("scan not found")
    return s


def promote(scan_id: str, reason: str, actor: str) -> dict:
    s = _scan(scan_id)
    if s.get("feedback") != "safe":
        raise Conflict("only scans that a person marked as safe can be reviewed here")
    n = normalize(s["url"])
    if is_shared_hosting(n.host):
        raise ValueError(f"{n.host} is a shared hosting platform: one good page says nothing about the other sites on it, so it cannot be allowlisted")
    if threat_features(n).get("threat_listed") == 1:
        raise Conflict("this domain is in a known threat feed, so it cannot be allowlisted")
    if allowlist_repo.is_allowlisted(n.host):
        raise Conflict(f"{n.host} is already allowlisted")
    allowlist_repo.add(n.host, reason, actor, scan_id)
    allowlist_repo.mark_reviewed(scan_id, "promoted", actor, reason)
    audit_service.record(actor, "allowlist.add", "domain", n.host, reason)
    return {"host": n.host, "status": "promoted"}


def dismiss(scan_id: str, reason: str, actor: str) -> dict:
    s = _scan(scan_id)
    allowlist_repo.mark_reviewed(scan_id, "dismissed", actor, reason)
    audit_service.record(actor, "feedback.dismiss", "scan", scan_id, reason)
    return {"host": s.get("url", ""), "status": "dismissed"}


def remove(host: str, actor: str, reason: str) -> None:
    if not allowlist_repo.remove(host):
        raise NotFound("that domain is not on the allowlist")
    audit_service.record(actor, "allowlist.remove", "domain", host, reason)
