"""Live sandbox test: launches the real headless browser against the staged pages.

Skipped unless FRAUDSHIELD_LIVE=1, so a normal pytest run never starts a browser. The staged pages are
served from a short-lived local server that lives and dies inside this test process.

Run:  FRAUDSHIELD_LIVE=1 FRAUDSHIELD_SANDBOX_ALLOW_HOSTS=127.0.0.1 python -m pytest tests/integration -s
"""
import functools
import http.server
import os
import threading
from pathlib import Path

import pytest

from app.engine.pipeline import run_pipeline
from app.sandbox.fetcher import fetch_page
from app.sandbox.policies import SandboxError

pytestmark = pytest.mark.skipif(os.environ.get("FRAUDSHIELD_LIVE") != "1", reason="set FRAUDSHIELD_LIVE=1 to run")

STAGED = Path(__file__).resolve().parents[3] / "data" / "samples" / "staged"


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redir":  # two hops, then the lookalike page
            self.send_response(302)
            self.send_header("Location", "/hop2")
            self.end_headers()
        elif self.path == "/probe":  # a hostile page that tries to make the browser reach internal addresses
            body = (
                b"<html><head><title>probe</title></head><body>"
                b'<img src="http://10.0.0.5/secret.png"><img src="http://169.254.169.254/latest/meta-data/">'
                b"</body></html>"
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/hop2":
            self.send_response(302)
            self.send_header("Location", "/lookalike_bank_login.html")
            self.end_headers()
        else:
            super().do_GET()

    def log_message(self, *args):  # keep test output quiet
        pass


@pytest.fixture(scope="module")
def base_url():
    handler = functools.partial(Handler, directory=str(STAGED))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)  # port 0 = any free port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def test_fetch_returns_the_real_page(base_url):
    snap = fetch_page(f"{base_url}/lookalike_bank_login.html")
    print("\n  title:", snap.title, "| status:", snap.status, "| chain:", snap.redirect_chain)
    assert snap.status == 200
    assert snap.title.startswith("ADCB Online Banking")
    assert 'type="password"' in snap.html
    assert snap.redirect_chain == (f"{base_url}/lookalike_bank_login.html",)


def test_redirect_chain_is_recorded(base_url):
    snap = fetch_page(f"{base_url}/redir")
    print("\n  chain:", snap.redirect_chain)
    assert len(snap.redirect_chain) == 3
    assert snap.final_url.endswith("/lookalike_bank_login.html")


def test_deep_scan_end_to_end(base_url):
    r = run_pipeline(f"{base_url}/lookalike_bank_login.html", deep=True)
    rules = {x["rule"] for x in r["reasons"]}
    print("\n  score:", r["score"], r["band"], "| rules:", sorted(rules))
    assert "sandbox" in r["analyzers_ok"]
    assert {"brand_plus_credential_form", "form_posts_to_other_domain", "urgency_language"} <= rules
    assert r["band"] == "likely_fraud"
    assert r["page"]["contacts"]["phones"] == ["+971501234567"]


def test_benign_page_is_safe_end_to_end(base_url):
    r = run_pipeline(f"{base_url}/plain_blog.html", deep=True)
    assert "sandbox" in r["analyzers_ok"] and r["page"]["title"].startswith("Visiting the Emirates")
    assert "brand_plus_credential_form" not in {x["rule"] for x in r["reasons"]}


def test_page_cannot_make_the_browser_reach_private_addresses(base_url):
    # The page itself is on the allowed host, but its images point at internal addresses.
    snap = fetch_page(f"{base_url}/probe")
    print("\n  allowed:", snap.network_hosts, "| blocked:", snap.blocked_hosts)
    assert {"10.0.0.5", "169.254.169.254"} <= set(snap.blocked_hosts)  # the guard fired
    assert "10.0.0.5" not in snap.network_hosts and "169.254.169.254" not in snap.network_hosts


def test_blocked_target_never_starts_a_browser():
    with pytest.raises(SandboxError, match="blocked"):
        fetch_page("http://169.254.169.254/latest/meta-data/")


def test_unreachable_page_raises_sandbox_error(monkeypatch):
    # nothing listens on this port; the fetch must fail cleanly instead of hanging or crashing
    monkeypatch.setenv("FRAUDSHIELD_SANDBOX_ALLOW_HOSTS", "127.0.0.1")
    with pytest.raises(SandboxError, match="fetch failed"):
        fetch_page("http://127.0.0.1:9/")
