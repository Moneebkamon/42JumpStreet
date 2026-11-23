"""Limits and safety rules for the sandbox browser.

The most important rule: the browser may only reach PUBLIC web addresses. Without it, anyone could
submit http://169.254.169.254/ or http://localhost:5432 and make the server fetch internal things.

Known limit: the address is checked when the request is made and the browser resolves DNS again, so a
hostile DNS server could answer differently the second time (DNS rebinding). The real fix is a network
rule on the sandbox container that blocks private ranges (infra/docker/sandbox.Dockerfile, later).
"""
import ipaddress
import os
import socket
from urllib.parse import urlsplit

NAV_TIMEOUT_MS = 15_000
MAX_HTML_BYTES = 2_000_000
BLOCKED_RESOURCE_TYPES = frozenset({"media", "font", "websocket", "eventsource"})
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class SandboxError(Exception):
    """The page could not be fetched safely (blocked, timed out, browser missing...)."""


def _allowed_hosts() -> set[str]:
    """Hosts that may be private. Empty in production. For local demos/tests only:
    FRAUDSHIELD_SANDBOX_ALLOW_HOSTS=localhost,127.0.0.1"""
    raw = os.environ.get("FRAUDSHIELD_SANDBOX_ALLOW_HOSTS", "")
    return {h.strip().lower() for h in raw.split(",") if h.strip()}


def is_public_url(url: str) -> bool:
    """True only for http(s) URLs whose every resolved address is a public one. Fails closed."""
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
    except ValueError:
        return False
    if parts.scheme in ("data", "blob", "about"):  # no network access
        return True
    if parts.scheme not in ("http", "https") or not host:
        return False
    if host in _allowed_hosts():
        return True
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False  # cannot resolve: do not fetch
    try:
        return all(ipaddress.ip_address(info[4][0].split("%")[0]).is_global for info in infos)
    except ValueError:
        return False
