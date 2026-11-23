"""Phone numbers, crypto wallet addresses and messaging handles shown on the page.

extract_contacts() returns the actual values (kept as evidence and later used to link sites into
campaigns); contact_features() returns only counts for scoring.
"""
import re

from app.analyzers.content_analyzer.page_doc import PageDoc
from app.analyzers.url_analyzer.normalizer import NormalizedURL

# UAE mobile / international style numbers, e.g. +971 50 123 4567, 00971501234567, 050-123-4567
_PHONE = re.compile(r"(?<!\d)(?:\+971|00971|0)\s?5\d[\s-]?\d{3}[\s-]?\d{4}(?!\d)")
_WALLET = re.compile(
    r"\b(?:bc1[a-z0-9]{25,60}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}|0x[a-fA-F0-9]{40}|T[1-9A-HJ-NP-Za-km-z]{33})\b"
)
_HANDLE_URL = re.compile(r"(?:wa\.me/|t\.me/|api\.whatsapp\.com/send\?phone=)([\w+]+)", re.I)


def _unique(items) -> list[str]:
    return list(dict.fromkeys(items))


def extract_contacts(doc: PageDoc) -> dict:
    hrefs = " ".join(a.get("href") or "" for a in doc.soup.find_all("a"))
    tel_links = [re.sub(r"\D", "", (a.get("href") or "")[4:]) for a in doc.soup.find_all("a", href=re.compile("^tel:", re.I))]
    phones = _unique([re.sub(r"[\s-]", "", m) for m in _PHONE.findall(doc.text)] + [t for t in tel_links if t])
    return {
        "phones": phones,
        "wallets": _unique(_WALLET.findall(doc.text)),
        "handles": _unique(_HANDLE_URL.findall(hrefs)),
    }


def contact_features(doc: PageDoc, n: NormalizedURL) -> dict:
    c = extract_contacts(doc)
    return {
        "content_num_phones": len(c["phones"]),
        "content_num_wallets": len(c["wallets"]),
        "content_num_handles": len(c["handles"]),
    }
