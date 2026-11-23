"""Public reports. Each one is scored by the same engine; a report raises triage priority but never blocks anything."""
from app.analyzers.url_analyzer.normalizer import normalize
from app.core.errors import NotFound, RateLimited
from app.core.rate_limit import SlidingWindowLimiter
from app.repositories import citizen_report_repo
from app.services import audit_service
from app.services.scan_service import scan_url

# 5 reports per 10 minutes per client on this server (in memory; see core/rate_limit.py)
limiter = SlidingWindowLimiter(max_hits=5, window_seconds=600)

ADVICE = {
    "safe": "Our automated check found no strong warning signs, but an analyst may still review your report.",
    "suspicious": "Our automated check found some warning signs. Do not enter passwords or card details on this site.",
    "high_risk": "Our automated check found several strong warning signs. Please do not open this link.",
    "likely_fraud": "This link very likely belongs to a scam. Please do not open it. Thank you for reporting it.",
}


def submit(url: str, note: str, contact: str, honeypot: str, client_key: str) -> dict:
    """Raises ValueError (bad input), RateLimited. A filled honeypot field is treated as a bot."""
    if honeypot.strip():
        raise ValueError("invalid submission")
    url, note, contact = url.strip(), note.strip(), contact.strip()
    if not url or len(url) > 2048 or len(note) > 1000 or len(contact) > 200:
        raise ValueError("invalid submission")
    host = normalize(url).host  # raises ValueError for an unusable link
    if not limiter.allow(client_key):
        raise RateLimited("Too many reports from this connection. Please try again later.")

    result = scan_url(url, deep=False)  # fast score only: the reported page is never opened
    ref = citizen_report_repo.add(result["url"], host, note, contact, result)
    audit_service.record("citizen", "report.submit", "report", ref, host)
    return {"ref": ref, "score": result["score"], "band": result["band"], "advice": ADVICE[result["band"]]}


def get_report(ref: str) -> dict:
    rep = citizen_report_repo.get(ref)
    if not rep:
        raise NotFound(f"report {ref} not found")
    return rep
