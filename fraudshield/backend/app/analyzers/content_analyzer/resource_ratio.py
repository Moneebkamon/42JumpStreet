"""Hidden iframes, obfuscated scripts and how much of the page is loaded from other domains."""
import re
from urllib.parse import urljoin

from app.analyzers.content_analyzer.form_inspector import _registered
from app.analyzers.content_analyzer.page_doc import PageDoc
from app.analyzers.url_analyzer.normalizer import NormalizedURL

_OBFUSCATION = re.compile(r"eval\s*\(|atob\s*\(|unescape\s*\(|String\.fromCharCode")
_HIDDEN_STYLE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.I)


def _is_hidden_iframe(el) -> bool:
    if el.has_attr("hidden") or _HIDDEN_STYLE.search(el.get("style") or ""):
        return True
    return (el.get("width") or "").strip() in ("0", "1") or (el.get("height") or "").strip() in ("0", "1")


def resource_features(doc: PageDoc, n: NormalizedURL) -> dict:
    total = external = 0
    for tag, attr in (("script", "src"), ("img", "src"), ("link", "href"), ("iframe", "src")):
        for el in doc.soup.find_all(tag):
            if tag == "link" and "stylesheet" not in (el.get("rel") or []):
                continue
            value = (el.get(attr) or "").strip()
            if not value:
                continue
            total += 1
            if value.startswith(("http://", "https://", "//")):
                reg = _registered(urljoin(doc.snapshot.final_url, value))
                if reg and reg != doc.final.registered_domain:
                    external += 1

    obfuscated = sum(
        1 for s in doc.soup.find_all("script") if not s.get("src") and _OBFUSCATION.search(s.string or s.get_text() or "")
    )
    return {
        "content_external_resource_ratio": round(external / total, 2) if total else 0.0,
        "content_hidden_iframes": sum(_is_hidden_iframe(f) for f in doc.soup.find_all("iframe")),
        "content_obfuscated_scripts": obfuscated,
    }
