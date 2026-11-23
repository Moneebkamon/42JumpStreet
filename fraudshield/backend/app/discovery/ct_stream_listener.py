"""Sources of certificate events. Every source yields dicts: {seq, issued_at (ISO, UTC), domains: [...], ...}.

- replay_source: reads a recorded/simulated .jsonl file (the demo and the tests use this).
- live_source: reads a certstream-compatible server (infra/certstream, self-hosted, read-only) over a websocket.
  parse_message treats everything it receives as untrusted text. for_seconds slices the endless stream into runs.
- with_reconnect: restarts a source that dies, with backoff and a retry cap.
- rate_capped: limits how many events per second flow downstream.
"""
import json
import os
import time
from collections.abc import Callable, Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SAMPLE = Path(__file__).resolve().parents[3] / "data" / "samples" / "ct_stream.jsonl"


def replay_source(path: Path | str = DEFAULT_SAMPLE) -> Iterator[dict]:
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


MAX_DOMAINS_PER_MESSAGE = 200
MAX_DOMAIN_LEN = 253


def parse_message(raw: str | bytes) -> dict | None:
    """One websocket message from a certstream server -> {"issued_at", "domains"} or None.

    The stream is untrusted text from the internet: anything unexpected is dropped, nothing is ever opened or executed.
    Accepts the "domains-only" shape (data is a list of names) and the lite/full shape (data.leaf_cert.all_domains).
    """
    try:
        msg = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(msg, dict):
        return None
    data, seen = msg.get("data"), None
    if isinstance(data, dict):
        seen = data.get("seen")
        leaf = data.get("leaf_cert")
        data = leaf.get("all_domains") if isinstance(leaf, dict) else None
    if not isinstance(data, list):
        return None
    domains = [d for d in data[:MAX_DOMAINS_PER_MESSAGE] if isinstance(d, str) and 0 < len(d) <= MAX_DOMAIN_LEN]
    if not domains:
        return None
    issued = datetime.fromtimestamp(seen, timezone.utc) if isinstance(seen, (int, float)) and seen > 0 else datetime.now(timezone.utc)
    return {"issued_at": issued.strftime("%Y-%m-%dT%H:%M:%SZ"), "domains": domains}


def live_source(url: str | None = None) -> Iterator[dict]:
    """Read new certificates from a certstream-compatible server (see infra/certstream). Read-only: sends nothing.

    Ends with ConnectionError when the server closes, so with_reconnect starts a new connection."""
    from websockets.sync.client import connect

    url = url or os.environ.get("FRAUDSHIELD_CT_URL", "ws://certstream:8080/domains-only")
    with connect(url, open_timeout=15, max_size=2**20, ping_interval=20, ping_timeout=30,
                 user_agent_header="fraudshield-ct-listener/0.1") as ws:
        for raw in ws:
            event = parse_message(raw)
            if event:
                yield event
    raise ConnectionError("certificate stream closed by the server")


def for_seconds(events: Iterable[dict], seconds: float, clock: Callable[[], float] = time.monotonic) -> Iterator[dict]:
    """Stop after `seconds` of wall time (checked as events arrive), so ingest() can record a heartbeat run."""
    deadline = clock() + seconds
    for event in events:
        yield event
        if clock() >= deadline:
            return


def with_reconnect(
    factory: Callable[[], Iterable[dict]],
    max_retries: int = 5,
    backoff_seconds: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> Iterator[dict]:
    """Yield from factory(); if it raises, wait (doubling each time) and start a new one.

    Gives up (re-raises) after max_retries consecutive failures. A source that yields at least
    one event resets the failure count. A source that ends normally ends the stream.
    """
    failures = 0
    while True:
        try:
            for event in factory():
                failures = 0
                yield event
            return
        except NotImplementedError:
            raise
        except Exception:
            failures += 1
            if failures > max_retries:
                raise
            sleep(backoff_seconds * 2 ** (failures - 1))


def rate_capped(
    events: Iterable[dict],
    max_per_second: float | None,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> Iterator[dict]:
    """Pace events to at most max_per_second. None means no cap."""
    if not max_per_second:
        yield from events
        return
    gap = 1.0 / max_per_second
    next_ok = clock()
    for event in events:
        wait = next_ok - clock()
        if wait > 0:
            sleep(wait)
        next_ok = max(next_ok, clock()) + gap
        yield event
