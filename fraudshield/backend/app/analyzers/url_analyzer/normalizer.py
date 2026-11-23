"""One canonical form of a URL. Every other URL analyzer works on this."""
import ipaddress
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit

import tldextract

# Offline: use the bundled public-suffix snapshot, never fetch it at runtime.
_extract = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)

_TRACKING_EXACT = {"fbclid", "gclid", "msclkid", "mc_cid", "mc_eid", "igshid"}


@dataclass(frozen=True)
class NormalizedURL:
    original: str
    url: str
    scheme: str
    scheme_assumed: bool
    host: str  # lowercase, ASCII (punycode) form
    host_unicode: str  # lowercase, Unicode form (for lookalike analysis)
    subdomain: str
    domain: str  # registrable label without the suffix
    suffix: str
    registered_domain: str
    path: str
    query: str
    port: int | None
    is_ip: bool


def _is_tracking(key: str) -> bool:
    k = key.lower()
    return k.startswith("utm_") or k in _TRACKING_EXACT


def normalize(raw: str) -> NormalizedURL:
    """Parse and canonicalize a URL. Raises ValueError for unusable input."""
    original = raw
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("empty url")

    scheme_assumed = "://" not in raw
    if scheme_assumed:
        raw = "https://" + raw

    try:
        parts = urlsplit(raw)
        port = parts.port
    except ValueError as exc:
        raise ValueError(f"invalid url: {exc}") from exc

    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        raise ValueError("url has no host")

    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError:
        ascii_host = host
    try:
        unicode_host = ascii_host.encode("ascii").decode("idna")
    except UnicodeError:
        unicode_host = host

    try:
        ipaddress.ip_address(ascii_host)
        is_ip = True
    except ValueError:
        is_ip = False

    scheme = parts.scheme.lower()
    if port in (80, 443):
        port = None

    query = urlencode([(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _is_tracking(k)])
    path = parts.path or "/"

    if is_ip:
        subdomain, domain, suffix, registered = "", ascii_host, "", ascii_host
    else:
        ext = _extract(ascii_host)
        subdomain, domain, suffix = ext.subdomain, ext.domain, ext.suffix
        registered = f"{domain}.{suffix}" if suffix else ascii_host

    netloc = ascii_host + (f":{port}" if port else "")
    url = f"{scheme}://{netloc}{path}" + (f"?{query}" if query else "")

    return NormalizedURL(
        original=original, url=url, scheme=scheme, scheme_assumed=scheme_assumed,
        host=ascii_host, host_unicode=unicode_host, subdomain=subdomain, domain=domain,
        suffix=suffix, registered_domain=registered, path=path, query=query, port=port, is_ip=is_ip,
    )
