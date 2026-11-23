# Stage 08: Proactive Discovery (Early Detection)

## Goal
Find suspicious domains before anyone reports them: consume certificate-transparency logs, filter cheaply, score the survivors automatically, pre-warm the cache and feed the live feed. (🟨 Feeding the extension blocklist is deferred.)

## Depends on
Stages 02-04 (scoring and analyzers), 03 (workers).

## Components and their single jobs
| Component | Job | Location |
|---|---|---|
| CT stream listener | Receive newly issued certificate domains continuously | `discovery/ct_stream_listener.py` |
| Prefilter | Discard ~99% cheaply: keep brand names, keywords, homoglyphs, risky patterns | `discovery/prefilter.py` |
| Domain watch | Track candidates, schedule scans and re-scans | `discovery/domain_watch.py` |
| Discovery tasks | Background jobs: ingest, score, re-scan | `workers/tasks/discovery_tasks.py`, `rescan_tasks.py` |
| Scheduler | Periodic feed refresh and re-scans | Celery beat config in `workers/celery_app.py` |
| Feed endpoint | Serve the latest detections to the dashboard | `api/v1/endpoints/feed.py` |
| 🟨 Blocklist service **[EXT - DEFERRED]** | Build the compact confirmed-bad list | `services/blocklist_service.py`, `api/v1/endpoints/blocklist.py` |
| Live feed UI | Table of new detections with filters | `components/feed/live-feed-table.tsx`, `feed-filters.tsx` |
| Feed hook | Refresh the feed periodically | `hooks/use-live-feed.ts` |
| Dashboard page | KPIs, timeline, top impersonated brands | `src/app/(analyst)/console/page.tsx` |
| KPI/charts | Reusable charts | `components/charts/` |

## Pipeline
1. Listener receives a new certificate's domain names.
2. Prefilter keeps only domains matching brand names (and near-variants), sensitive keywords (login, verify, secure, wallet, etc.), homoglyph/punycode, or risky TLD patterns.
3. Survivors go to the scan queue with source `ct_feed`.
4. Fast score first; deep scan if suspicious or brand-related.
5. Store results; high-risk items enter the feed. 🟨 (Deferred: blocklist candidates for the extension.)
6. **Pre-warm the cache** so a later scan answers instantly. (🟨 The later `/check` from the extension is deferred.)
7. **Re-scan** flagged domains after about 24 hours (pages often switch on later).

## Tasks
1. Implement the listener with reconnect handling and a rate cap.
2. Implement the prefilter using `config/brands.yaml` and `config/tld_risk.yaml`; measure the pass-through rate.
3. Implement domain watch and discovery/re-scan tasks; add beat schedule.
4. Implement the feed endpoint. 🟨 **[EXTENSION - DEFERRED]** ~~and blocklist endpoint~~.
5. Build the live feed table, filters and dashboard KPIs.
6. Store the source and detection time so you can show **time from certificate issue to detection**.
7. Fallback: a recorded sample stream in `data/samples/` so the demo works without the live feed.

## Interfaces
- `GET /feed` (filters: score, brand, source, status), `GET /stats`.
- 🟨 `GET /blocklist` **[EXTENSION - DEFERRED]**

## Done when
- New suspicious domains appear in the feed automatically with score and reasons.
- The pass-through rate and processing latency are measured and documented.
- A flagged domain is later answered instantly from the cache when scanned. 🟨 (`/check` for the extension is deferred.)
- The demo can run from the recorded sample stream.

## Risks and cut-lines
- Load: cap scans per minute; queue priority for brand matches.
- False positives from the prefilter: it only selects candidates; the scoring engine decides.
- Cut-line: skip re-scans; keep listener, prefilter, auto-score, feed. 🟨 The blocklist export is deferred with the extension.

## Time estimate
About 4 hours.
