# Proactive discovery (stage 08)

Finds suspicious domains from newly issued certificates before anyone reports them.

```
certificate events -> prefilter -> score (URL/domain only) -> SQLite -> /feed, /stats, Telegram alert
                                                                 \-> pre-warmed cache for /scan
```

## Parts
| Part | File |
|---|---|
| Sources (replay, reconnect, rate cap; live is a stub) | `backend/app/discovery/ct_stream_listener.py` |
| Prefilter | `backend/app/discovery/prefilter.py` |
| Ingest loop and timing | `backend/app/discovery/ingest.py` |
| Store (SQLite, temporary until stage 03) | `backend/app/discovery/domain_watch.py` |
| Alerts | `backend/app/alerts/` (off unless `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set) |
| API | `GET /api/v1/feed` (`min_score`, `brand`, `source`, `status`, `limit`), `GET /api/v1/stats` |
| UI | `/console` (`frontend/src/components/feed/`) |

## Run the demo
```
backend/.venv/Scripts/python scripts/generate_ct_sample.py     # only to regenerate the sample
backend/.venv/Scripts/python scripts/run_discovery.py --reset  # replay, score, store, print figures
yarn backend ; yarn frontend                                   # then open http://localhost:3000/console
```

## Measured on the simulated sample (986 events, seed 42)
The sample is **invented** (`data/samples/ct_stream.jsonl`, every line has `"simulated": true`). It is not a recording
of a real certificate log, so these numbers describe the code on planted data, not real-world performance.

| Figure | Value |
|---|---|
| Prefilter pass-through | 8.3% (82 of 986). Inflated: ~10% of the sample is planted scams by construction. A real stream is mostly benign. |
| Planted brand lookalikes kept | 47 of 49 (95.9%). Both misses are `ad1b.*` (digit `1` used for `i`; the skeleton maps `1` to `l` only) |
| Keyword and homoglyph plants kept | 25 of 25 and 10 of 10 |
| Benign kept (false candidates) | 0 of 896 |
| Official brand domains kept | 0 of 6 |
| Scoring time per domain | about 3 ms (URL-only, no network) |
| Scores of survivors | 37 safe, 37 suspicious, 7 high risk, 1 likely fraud |

Keyword-only domains score 15 and homoglyph-only 25 ("safe") because nothing in them names a brand. They are kept as
candidates for a later deep scan; the feed hides them by default (min score 30).

**Issue-to-detection time.** For a replayed sample this is only the processing time (the certificate times are in the
past), so it is shown as simulated. It becomes meaningful only with a live stream.

## Not built yet
Live certificate stream, Celery workers and beat, 24-hour re-scans, deep scan of flagged domains, blocklist export
(deferred with the extension).
