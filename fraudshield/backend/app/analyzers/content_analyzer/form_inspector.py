"""Password / payment fields and where a form sends its data. Keys start with content_.

content_form_cross_domain counts only forms that hold a password or payment field, because many
legitimate pages post harmless forms (search, newsletter) to other domains.
"""
import re
from urllib.parse import urljoin

from app.analyzers.content_analyzer.page_doc import PageDoc
from app.analyzers.url_analyzer.normalizer import NormalizedURL, normalize

_PAYMENT_HINT = re.compile(r"card|cvv|cvc|iban|expir|ccnum", re.I)
_IGNORED_ACTIONS = ("javascript:", "#", "mailto:", "tel:")


def _has_password(inputs) -> bool:
    return any((i.get("type") or "").lower() == "password" for i in inputs)


def _has_payment(inputs) -> bool:
    for i in inputs:
        if (i.get("autocomplete") or "").lower().startswith("cc-"):
            return True
        if _PAYMENT_HINT.search(" ".join(str(i.get(a) or "") for a in ("name", "id", "placeholder"))):
            return True
    return False


def _registered(url: str) -> str | None:
    try:
        return normalize(url).registered_domain
    except ValueError:
        return None


def form_features(doc: PageDoc, n: NormalizedURL) -> dict:
    forms = doc.soup.find_all("form")
    page_inputs = doc.soup.find_all("input")
    cross = 0
    payment = _has_payment(page_inputs)
    for form in forms:
        inputs = form.find_all("input")
        if not (_has_password(inputs) or _has_payment(inputs)):
            continue
        action = (form.get("action") or "").strip()
        if not action or action.lower().startswith(_IGNORED_ACTIONS):
            continue
        target = _registered(urljoin(doc.snapshot.final_url, action))
        if target and target != doc.final.registered_domain:
            cross = 1
    return {
        "content_num_forms": len(forms),
        "content_has_credential_form": int(_has_password(page_inputs)),
        "content_has_payment_form": int(payment),
        "content_form_cross_domain": cross,
    }
