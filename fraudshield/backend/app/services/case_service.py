"""Case lifecycle: open a case from a scan, a discovered domain or a citizen report, move it through its statuses."""
from app.analyzers.url_analyzer.normalizer import normalize
from app.core.constants import OPEN_STATUSES, STATUS_NEW, TRANSITIONS
from app.core.errors import Conflict, InvalidTransition, NotFound
from app.discovery import domain_watch
from app.repositories import action_repo, case_repo, citizen_report_repo, evidence_repo, scan_repo
from app.services import audit_service, priority_service

SOURCES = ("scan", "detection", "report")
MIN_REASON = 3


def _load_source(source: str, source_ref: str) -> dict:
    """Return the stored scan result the case is built on. Raises NotFound / ValueError."""
    if source == "scan":
        result = scan_repo.get(source_ref)
    elif source == "detection":
        result = domain_watch.cached_result(source_ref)
    elif source == "report":
        rep = citizen_report_repo.get(source_ref)
        result = rep["result"] if rep else None
    else:
        raise ValueError(f"source must be one of {SOURCES}")
    if result is None:
        raise NotFound(f"no {source} found for {source_ref}")
    return result


def create_case(source: str, source_ref: str, actor: str, title: str | None = None) -> dict:
    result = _load_source(source, source_ref)
    host = normalize(result["url"]).host
    existing = case_repo.open_case_for_host(host, OPEN_STATUSES)
    if existing:
        raise Conflict(f"A case for {host} is already open ({existing}).", ref=existing)

    feats = result.get("features", {})
    impersonating = bool(feats.get("brand_impersonation"))
    brand_id = feats.get("brand_id", "") if impersonating else ""
    brand_name = feats.get("brand_name", "") if impersonating else ""
    prio = priority_service.compute(result["score"], brand_id, host)["priority"]
    ref = case_repo.create(
        title=(title or f"Suspected scam site: {host}").strip()[:200], url=result["url"], host=host, source=source,
        source_ref=source_ref, status=STATUS_NEW, priority=prio, score=result["score"], band=result["band"],
        brand_id=brand_id, brand_name=brand_name, result=result, actor=actor,
    )
    audit_service.record(actor, "case.create", "case", ref, f"from {source} {source_ref}")
    return get_case(ref)


def get_case(ref: str) -> dict:
    case = case_repo.get(ref)
    if not case:
        raise NotFound(f"case {ref} not found")
    return case


def case_detail(ref: str) -> dict:
    case = get_case(ref)
    return {
        **case,
        "events": case_repo.events(ref),
        "evidence": evidence_repo.list_for_case(ref),
        "takedown_drafts": action_repo.list_drafts(ref),
        "allowed_next": list(TRANSITIONS.get(case["status"], ())),
    }


def change_status(ref: str, to_status: str, reason: str, actor: str) -> dict:
    case = get_case(ref)
    reason = (reason or "").strip()
    if len(reason) < MIN_REASON:
        raise ValueError("a reason is required for every status change")
    allowed = TRANSITIONS.get(case["status"], ())
    if to_status not in allowed:
        raise InvalidTransition(
            f"cannot move from {case['status']} to {to_status}"
            + (f"; allowed: {', '.join(allowed)}" if allowed else "; this case is final")
        )
    case_repo.set_status(ref, case["status"], to_status, actor, reason)
    audit_service.record(actor, "case.status", "case", ref, f"{case['status']} -> {to_status}: {reason}")
    return case_detail(ref)


def add_note(ref: str, text: str, actor: str) -> dict:
    get_case(ref)
    text = (text or "").strip()
    if not text:
        raise ValueError("note is empty")
    case_repo.add_event(ref, "note", actor, text[:2000])
    audit_service.record(actor, "case.note", "case", ref)
    return case_detail(ref)
