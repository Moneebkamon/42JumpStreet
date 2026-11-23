"""Detect lookalike characters and punycode. Keys start with url_.

`skeleton()` is also used later to compare a host against brand names.
"""
import re
import unicodedata

from app.analyzers.url_analyzer.normalizer import NormalizedURL

# Characters that look like a Latin letter. Non-ASCII ones are written as escapes.
_CONFUSABLE_NON_ASCII = {
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c",
    "х": "x", "у": "y", "і": "i", "ј": "j", "ԁ": "d",
    "ɡ": "g", "ο": "o", "α": "a", "ν": "v", "ρ": "p",
    "ı": "i", "ᴀ": "a",
}
# ASCII look-alikes (leet speak). Applied only when building a skeleton.
_CONFUSABLE_ASCII = {"0": "o", "1": "l", "3": "e", "5": "s", "$": "s"}
_MULTI = (("rn", "m"), ("vv", "w"))

_LEET = re.compile(r"[a-z][0135]|[0135][a-z]")


def skeleton(host: str) -> str:
    """Reduce lookalike characters to a plain form so 'paypa1' and 'paypal' compare equal."""
    s = unicodedata.normalize("NFKC", host.lower())
    s = "".join(_CONFUSABLE_NON_ASCII.get(ch, _CONFUSABLE_ASCII.get(ch, ch)) for ch in s)
    for src, dst in _MULTI:
        s = s.replace(src, dst)
    return s


def _scripts(label: str) -> set[str]:
    out = set()
    for ch in label:
        if ch.isalpha():
            out.add(unicodedata.name(ch, "UNKNOWN").split(" ")[0])
    return out


def homoglyph_features(n: NormalizedURL) -> dict:
    labels = n.host_unicode.split(".")
    mixed = any("LATIN" in _scripts(lb) and len(_scripts(lb)) > 1 for lb in labels)
    non_ascii = [ch for ch in n.host_unicode if ord(ch) > 127]
    return {
        "url_has_punycode": int("xn--" in n.host),
        "url_has_non_ascii": int(bool(non_ascii)),
        "url_mixed_script": int(mixed),
        "url_confusable_chars": sum(ch in _CONFUSABLE_NON_ASCII for ch in non_ascii),
        "url_leet_digits": int(bool(_LEET.search(n.domain))),
    }
