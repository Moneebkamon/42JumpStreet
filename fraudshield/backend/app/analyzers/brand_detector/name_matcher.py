"""Does the URL use a protected brand's name without owning the domain? Keys start with brand_.

Matching rules (kept strict to limit false positives):
- short tokens (under 4 chars, e.g. "du", "dib") match only as a whole word between - . _
- tokens of 4+ chars also match as a substring of the domain label / subdomain
- one-edit typos only for tokens of 6+ chars (so "team.com" is not a typo of "tamm")
- a brand name found only in the path counts, but ranks lowest
"""
import re
from dataclasses import dataclass

from app.analyzers.brand_detector.ownership_check import official_brand
from app.analyzers.content_analyzer.page_doc import PageDoc
from app.analyzers.brand_detector.registry import Brand, get_brands
from app.analyzers.url_analyzer.homoglyph import skeleton
from app.analyzers.url_analyzer.normalizer import NormalizedURL

_SPLIT = re.compile(r"[.\-_]")
_WHERE_RANK = {"path": 1, "subdomain": 2, "domain": 3}
_KIND_RANK = {"typo": 1, "substring": 2, "exact": 3}


@dataclass(frozen=True)
class BrandMatch:
    brand: Brand
    where: str  # domain | subdomain | path
    kind: str  # exact | substring | typo


def _parts(text: str) -> list[str]:
    return [skeleton(p) for p in _SPLIT.split(text) if p]


def _edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _one_edit_apart(a: str, b: str) -> bool:
    """True when the Levenshtein distance is exactly 1 (one substitution, insertion or deletion). Linear time:
    the full edit-distance table was the hot spot when scoring thousands of certificate names per second."""
    la, lb = len(a), len(b)
    if abs(la - lb) > 1 or a == b:
        return False
    i = 0
    while i < la and i < lb and a[i] == b[i]:
        i += 1
    if la == lb:
        return a[i + 1:] == b[i + 1:]
    if la < lb:
        return a[i:] == b[i + 1:]
    return a[i + 1:] == b[i:]


# A brand name buried in a long label is almost always junk (random probes, generated test hosts), not an
# impersonation: "adcbanotexists32543210qvznfiyx". Substring hits need a label no longer than the token + this many characters.
MAX_EXTRA_CHARS = 14


SHORT_TOKEN = 6  # tokens shorter than this must sit at the start or end of a label ("ladibay" is not "adib")


def _ignored(part: str, ignore: frozenset[str]) -> bool:
    return any(part.startswith(w) for w in ignore)


def _substring_hit(token: str, p: str) -> bool:
    if token not in p or len(p) - len(token) > MAX_EXTRA_CHARS:
        return False
    return len(token) >= SHORT_TOKEN or p.startswith(token) or p.endswith(token)


def _kind(token: str, whole: str, parts: list[str], substring_ok: bool = True, ignore: frozenset[str] = frozenset()) -> str | None:
    if token in parts:
        return "exact"
    if substring_ok and len(token) >= 4 and any(_substring_hit(token, p) and not _ignored(p, ignore) for p in parts):
        return "substring"
    if len(token) >= 6 and any(_one_edit_apart(token, p) for p in parts + [whole] if p and not _ignored(p, ignore)):
        return "typo"
    return None


def find_brand_match(n: NormalizedURL) -> BrandMatch | None:
    areas = (
        ("domain", skeleton(n.domain), _parts(n.domain)),
        ("subdomain", skeleton(n.subdomain), _parts(n.subdomain)),
    )
    path_text = skeleton(f"{n.path}?{n.query}".lower())
    best: tuple | None = None
    for brand in get_brands():
        for raw_token in brand.tokens:
            token = skeleton(raw_token)
            sub_ok = raw_token not in brand.exact_only
            ignore = frozenset(skeleton(w) for w in brand.ignore_words)
            # very short names (moi, du, fab, dib) are ordinary words in other languages: only trust them in the
            # registered domain, never in a subdomain label
            candidates = [
                (w, _kind(token, whole, parts, sub_ok, ignore))
                for w, whole, parts in areas
                if not (len(token) < 4 and w == "subdomain")
            ]
            if sub_ok and len(token) >= 4 and token in path_text:
                candidates.append(("path", "substring"))
            for where, kind in candidates:
                if kind is None:
                    continue
                # longer (more specific) token wins over match kind: "emiratesnbs" is a typo of
                # "emiratesnbd", not a substring hit on the shorter "emirates"
                rank = (_WHERE_RANK[where], len(token), _KIND_RANK[kind])
                if best is None or rank > best[0]:
                    best = (rank, BrandMatch(brand, where, kind))
    return best[1] if best else None


def brand_features(n: NormalizedURL) -> dict:
    """brand_id / brand_name are text labels; everything else is numeric 0/1."""
    empty = {
        "brand_match": 0, "brand_id": "", "brand_name": "", "brand_is_official": 0,
        "brand_impersonation": 0, "brand_typosquat": 0,
        "brand_in_domain": 0, "brand_in_subdomain": 0, "brand_in_path": 0,
    }
    owner = official_brand(n.host)
    if owner:
        return {**empty, "brand_match": 1, "brand_id": owner.id, "brand_name": owner.name_en, "brand_is_official": 1}
    m = find_brand_match(n)
    if not m:
        return empty
    return {
        **empty,
        "brand_match": 1, "brand_id": m.brand.id, "brand_name": m.brand.name_en,
        "brand_impersonation": 1, "brand_typosquat": int(m.kind == "typo"),
        "brand_in_domain": int(m.where == "domain"),
        "brand_in_subdomain": int(m.where == "subdomain"),
        "brand_in_path": int(m.where == "path"),
    }


def page_brand_features(doc: PageDoc, n: NormalizedURL) -> dict:
    """Does the PAGE present itself as a protected brand while living on a domain that is not its own?

    Only the title, headings and image alt text count. Body text is ignored because ordinary pages
    mention names like "Emirates" all the time. Keys: brand_page_claim, brand_page_id, brand_page_name.
    """
    none = {"brand_page_claim": 0, "brand_page_id": "", "brand_page_name": ""}
    if official_brand(n.host) or official_brand(doc.final.host):
        return none

    parts = [doc.title] + [h.get_text(" ", strip=True) for h in doc.soup.find_all(["h1", "h2", "h3"])]
    parts += [img.get("alt") or "" for img in doc.soup.find_all("img")]
    claim_text = " ".join(parts)
    low = claim_text.lower()

    best: tuple[int, Brand] | None = None
    for brand in get_brands():
        names = [brand.name_en.lower()] + [t for t in brand.tokens if len(t) >= 4]
        hits = [len(nm) for nm in names if re.search(rf"(?<![a-z0-9]){re.escape(nm)}(?![a-z0-9])", low)]
        if brand.name_ar and brand.name_ar in claim_text:
            hits.append(len(brand.name_ar))
        if hits and (best is None or max(hits) > best[0]):
            best = (max(hits), brand)
    if not best:
        return none
    return {"brand_page_claim": 1, "brand_page_id": best[1].id, "brand_page_name": best[1].name_en}
