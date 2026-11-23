"""Load a suspicious URL in an isolated headless browser and return a PageSnapshot.

Rules enforced here: public addresses only (every request, including redirects and sub-resources),
no downloads, dialogs dismissed, no forms are ever filled or submitted, hard time and size limits.
Playwright is imported lazily so the rest of the backend works without it installed.
"""
from urllib.parse import urlsplit

from app.sandbox.policies import (
    BLOCKED_RESOURCE_TYPES, MAX_HTML_BYTES, NAV_TIMEOUT_MS, USER_AGENT, SandboxError, is_public_url,
)
from app.sandbox.snapshot import PageSnapshot


def fetch_page(url: str) -> PageSnapshot:
    """Raises SandboxError if the URL is blocked or the page cannot be loaded."""
    if not is_public_url(url):
        raise SandboxError("blocked: not a public web address")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SandboxError("playwright is not installed") from exc

    hosts: set[str] = set()
    blocked: set[str] = set()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                # Certificate errors are ignored on purpose: scam sites often have bad ones and we still
                # want to look at them. Nothing here is trusted or submitted.
                ctx = browser.new_context(
                    user_agent=USER_AGENT, accept_downloads=False, ignore_https_errors=True, service_workers="block"
                )
                page = ctx.new_page()
                page.on("dialog", lambda d: d.dismiss())

                def guard(route):
                    req = route.request
                    host = urlsplit(req.url).hostname or ""
                    if req.resource_type in BLOCKED_RESOURCE_TYPES:
                        return route.abort()
                    if not is_public_url(req.url):
                        blocked.add(host or req.url[:40])
                        return route.abort()
                    hosts.add(host)
                    return route.continue_()

                ctx.route("**/*", guard)
                response = page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)

                chain: list[str] = []
                if response is not None:
                    req = response.request
                    while req is not None:
                        chain.append(req.url)
                        req = req.redirected_from
                    chain.reverse()
                if not chain:
                    chain = [url]
                final_url = page.url
                if chain[-1] != final_url:  # JavaScript / meta-refresh redirect
                    chain.append(final_url)

                raw = page.content().encode("utf-8", errors="ignore")
                return PageSnapshot(
                    requested_url=url,
                    final_url=final_url,
                    status=response.status if response is not None else None,
                    title=page.title(),
                    html=raw[:MAX_HTML_BYTES].decode("utf-8", errors="ignore"),
                    redirect_chain=tuple(chain),
                    network_hosts=tuple(sorted(h for h in hosts if h)),
                    blocked_hosts=tuple(sorted(blocked)),
                    truncated=len(raw) > MAX_HTML_BYTES,
                )
            finally:
                browser.close()
    except SandboxError:
        raise
    except Exception as exc:  # timeouts, crashes, navigation errors
        raise SandboxError(f"fetch failed: {type(exc).__name__}") from exc
