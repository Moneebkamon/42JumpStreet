"""Free-hosting and popularity signals read from the link text. Keys: url_free_hosting, url_generated_label, url_domain_popular.

- url_domain_popular: the registered domain is in the bundled Tranco top-5000 list (config/popular_domains.txt). Used only to
  avoid brand-name false alarms on well-known sites (amazonaws.com, office.net...). Well-known does not mean safe.
- url_generated_label: the page sits on a free hosting service (pages.dev, vercel.app...) and its name looks machine-generated
  (several short random code groups, or a date), the way phishing kits name pages. Honest limit: ordinary preview deployments
  can look similar, so the rule is weighted below the brand rules and has not been measured on real legitimate free-hosting pages.
"""
import re
from functools import lru_cache

from app.analyzers.threat_intel.feed_lookup import SHARED_HOSTING
from app.analyzers.url_analyzer.normalizer import NormalizedURL
from app.core.config import CONFIG_DIR

_DATE = re.compile(r"(?<!\d)\d{2}-\d{2}-20\d{2}(?!\d)")


@lru_cache(maxsize=1)
def _popular() -> frozenset[str]:
    try:
        lines = (CONFIG_DIR / "popular_domains.txt").read_text(encoding="utf-8").splitlines()
    except OSError:
        return frozenset()
    return frozenset(x.strip() for x in lines if x.strip() and not x.startswith("#"))


def _host_label(host: str) -> str | None:
    """The part left of the free-hosting domain, or None when the host is not on one."""
    for d in SHARED_HOSTING:
        if host.endswith("." + d):
            return host[: -len(d) - 1]
    return None


def _looks_generated(label: str) -> bool:
    label = label.split(".")[-1]  # the label next to the hosting domain
    if _DATE.search(label):
        return True
    groups = [g for g in label.split("-") if g]
    mixed = [g for g in groups if re.search(r"[a-z]", g) and re.search(r"\d", g)]
    return len(groups) >= 4 and len(mixed) >= 2 and all(len(g) <= 8 for g in groups[:4])


def hosting_features(n: NormalizedURL) -> dict:
    label = _host_label(n.host)
    return {
        "url_domain_popular": int(n.registered_domain in _popular()),
        "url_free_hosting": int(label is not None),
        "url_generated_label": int(label is not None and _looks_generated(label)),
    }
