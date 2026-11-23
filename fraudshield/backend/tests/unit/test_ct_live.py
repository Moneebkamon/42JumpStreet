import json

from app.discovery.ct_stream_listener import for_seconds, parse_message


def test_domains_only_message_is_parsed():
    ev = parse_message(json.dumps({"message_type": "dns_entries", "data": ["a.example.com", "www.a.example.com"]}))
    assert ev["domains"] == ["a.example.com", "www.a.example.com"] and ev["issued_at"].endswith("Z")


def test_lite_message_uses_all_domains_and_seen_time():
    msg = {"message_type": "certificate_update", "data": {"seen": 1700000000.5, "leaf_cert": {"all_domains": ["x.example.org"]}}}
    ev = parse_message(json.dumps(msg))
    assert ev == {"issued_at": "2023-11-14T22:13:20Z", "domains": ["x.example.org"]}


def test_untrusted_garbage_is_dropped_not_raised():
    for raw in ("not json", "[]", "null", json.dumps({"data": "x"}), json.dumps({"data": [1, None, {}]}),
                json.dumps({"data": {"leaf_cert": "x"}}), json.dumps({"data": []}), b"\xff\xfe"):
        assert parse_message(raw) is None


def test_oversized_input_is_capped():
    ev = parse_message(json.dumps({"data": ["a.example.com"] * 1000 + ["x" * 300]}))
    assert len(ev["domains"]) == 200
    assert parse_message(json.dumps({"data": ["x" * 300]})) is None


def test_for_seconds_stops_after_the_deadline_but_keeps_the_source_alive():
    t = [0.0]
    source = iter(range(100))
    taken = list(for_seconds(({"n": n} for n in source), 3, clock=lambda: t.__setitem__(0, t[0] + 1) or t[0]))
    assert 1 <= len(taken) <= 4
    assert next(source) is not None  # source not exhausted


def test_checked_list_records_every_domain_and_is_capped(tmp_path, monkeypatch):
    from app.discovery import domain_watch
    from app.discovery.ingest import ingest

    monkeypatch.setenv("FRAUDSHIELD_NETWORK", "0")
    db = tmp_path / "d.db"
    events = [{"issued_at": "2026-11-20T08:00:00Z", "domains": ["plain-garden-shop.example", "adcb-secure-login.example.com"]}]
    ingest(events, source="test", simulated=True, notify=lambda d: False, db_file=db)
    rows = {r["domain"]: r for r in domain_watch.recent_checked(path=db)}
    assert rows["plain-garden-shop.example"]["kept"] is False and rows["plain-garden-shop.example"]["score"] is None
    flagged = rows["adcb-secure-login.example.com"]
    assert flagged["kept"] is True and flagged["score"] >= 30 and flagged["band"]

    many = [{"domain": f"d{i}.example", "checked_at": "2026-11-20T08:00:00Z", "source": "t", "simulated": False, "kept": False,
             "score": None, "band": "", "brand_name": ""} for i in range(domain_watch.CHECKED_KEEP + 50)]
    domain_watch.record_checked(many, db)
    assert len(domain_watch.recent_checked(limit=5000, path=db)) <= domain_watch.CHECKED_KEEP
