"""Takedown report DRAFTS for human review. This module only drafts and exports text; it never sends anything.

Wording says "suspected" unless an analyst has confirmed the case, and makes no statement about any person.
"""
from app.core.constants import STATUS_CONFIRMED, STATUS_NEW, STATUS_TAKEDOWN, STATUS_TAKEN_DOWN
from app.core.errors import Conflict, NotFound
from app.repositories import action_repo, case_repo, evidence_repo
from app.services import audit_service

RECIPIENTS = {
    "registrar_hosting": "Domain registrar / hosting provider",
    "search_safety": "Search engine / browser safety team",
    "brand": "Impersonated brand's security team",
    "telecom": "Telecom operator (SMS / number abuse)",
}
_CONFIRMED_STATES = (STATUS_CONFIRMED, STATUS_TAKEDOWN, STATUS_TAKEN_DOWN)

_ASK = {
    "registrar_hosting": "We ask you to review the site and, if it violates your abuse policy, suspend the domain or "
                         "the hosted content.",
    "search_safety": "We ask you to review the address for inclusion in your phishing / deceptive-site warnings.",
    "brand": "We are sharing this so you can assess it and, if you agree, request its removal through your own channels.",
    "telecom": "We ask you to review any numbers or messaging campaigns linked to this site under your abuse policy.",
}


def build_draft(case_ref: str, recipient_type: str, actor: str) -> dict:
    if recipient_type not in RECIPIENTS:
        raise ValueError(f"recipient_type must be one of {sorted(RECIPIENTS)}")
    case = case_repo.get(case_ref)
    if not case:
        raise NotFound(f"case {case_ref} not found")
    if case["status"] == STATUS_NEW:
        raise Conflict("Move the case to 'under review' before drafting a report.")

    confirmed = case["status"] in _CONFIRMED_STATES
    verdict = "an analyst-confirmed" if confirmed else "a suspected"
    reasons = [r["reason"] for r in case["result"].get("reasons", [])[:5]]
    evidence = evidence_repo.list_for_case(case_ref)

    lines = [
        f"To: {RECIPIENTS[recipient_type]}",
        f"Reference: {case_ref}",
        "",
        f"We are reporting {verdict} fraudulent website for your review.",
        "",
        f"Address: {case['url']}",
        f"Automated risk score: {case['score']}/100 ({case['band'].replace('_', ' ')})",
    ]
    if case["brand_name"]:
        lines.append(f"Possible impersonation of: {case['brand_name']}")
    lines += ["", "Why it was flagged:"] + [f"  - {r}" for r in reasons]
    lines += ["", "Evidence (SHA-256 of each frozen item):"]
    if evidence:
        lines += [f"  - {e['kind']}: {e['sha256']} (captured {e['captured_at']}, {e['tool_version']})" for e in evidence]
    else:
        lines.append("  - No evidence has been frozen yet. Freeze it on the case page before sending.")
    lines += [
        "", _ASK[recipient_type], "",
        "Status of this report: " + ("confirmed by an analyst." if confirmed
                                     else "AUTOMATED ASSESSMENT, NOT YET CONFIRMED by an analyst. Do not send before review."),
        "This is a draft prepared by FraudShield for human review; it has not been sent to anyone.",
    ]
    subject = f"{'Report' if confirmed else 'Suspected'} fraudulent website: {case['host']} [{case_ref}]"
    draft_id = action_repo.add_draft(case_ref, recipient_type, subject, "\n".join(lines), actor)
    case_repo.add_event(case_ref, "takedown_draft", actor, f"Drafted report for {RECIPIENTS[recipient_type]}")
    audit_service.record(actor, "takedown.draft", "case", case_ref, f"{recipient_type} draft {draft_id}")
    return action_repo.get_draft(draft_id)


def export(draft_id: int, actor: str) -> tuple[str, str]:
    """(filename, text) for download. Marks the draft exported and logs it. Does not send anything."""
    draft = action_repo.get_draft(draft_id)
    if not draft:
        raise NotFound(f"draft {draft_id} not found")
    action_repo.mark_exported(draft_id)
    audit_service.record(actor, "takedown.export", "case", draft["case_ref"], f"draft {draft_id}")
    text = f"Subject: {draft['subject']}\n\n{draft['body']}\n"
    return f"{draft['case_ref']}-{draft['recipient_type']}.txt", text
