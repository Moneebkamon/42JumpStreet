"""Freeze, hash, store and verify evidence. The system gives a tamper-evident record, not a legal opinion.

What is frozen comes from the analysis already stored on the case (the scan result): the full result, the reasons, the
analyzer features (domain age, DNS, TLS and similar lookups are inside them) and, for a deep scan, the redirect chain and
the hosts the page contacted. Screenshots and raw HTML are not captured yet (the sandbox does not take them).

Each item is stored as canonical JSON text and hashed with SHA-256 over its UTF-8 bytes. Verification recomputes the hash
from what is stored and compares it. Every freeze, view and verify is written to the audit log.
"""
import hashlib
import json

from app.core.constants import TOOL_VERSION
from app.core.errors import NotFound
from app.db.sqlite import now_utc
from app.repositories import case_repo, evidence_repo
from app.services import audit_service


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _items(result: dict) -> list[tuple[str, object]]:
    items: list[tuple[str, object]] = [
        ("scan_result", result),
        ("reasons", result.get("reasons", [])),
        ("features", result.get("features", {})),
    ]
    page = result.get("page")
    if page:
        items.append(("redirect_chain", page.get("redirect_chain", [])))
        items.append(("network_hosts", page.get("network_hosts", [])))
        items.append(("page_summary", {k: page.get(k) for k in ("final_url", "title", "status", "contacts")}))
    return items


def freeze(case_ref: str, actor: str) -> list[dict]:
    case = case_repo.get(case_ref)
    if not case:
        raise NotFound(f"case {case_ref} not found")
    captured = now_utc()
    for kind, obj in _items(case["result"]):
        text = canonical(obj)
        evidence_repo.add(case_ref, kind, text, sha256_hex(text), captured, TOOL_VERSION, actor)
    case_repo.add_event(case_ref, "evidence", actor, f"Evidence frozen at {captured}")
    audit_service.record(actor, "evidence.freeze", "case", case_ref, f"captured {captured}")
    return evidence_repo.list_for_case(case_ref)


def get_evidence(evidence_id: int, actor: str) -> dict:
    item = evidence_repo.get(evidence_id)
    if not item:
        raise NotFound(f"evidence {evidence_id} not found")
    audit_service.record(actor, "evidence.view", "evidence", evidence_id)
    return item


def verify(evidence_id: int, actor: str) -> dict:
    item = evidence_repo.get(evidence_id)
    if not item:
        raise NotFound(f"evidence {evidence_id} not found")
    recomputed = sha256_hex(item["content"])
    ok = recomputed == item["sha256"]
    audit_service.record(actor, "evidence.verify", "evidence", evidence_id, "match" if ok else "MISMATCH")
    return {"id": evidence_id, "ok": ok, "stored_sha256": item["sha256"], "recomputed_sha256": recomputed,
            "kind": item["kind"], "captured_at": item["captured_at"]}
