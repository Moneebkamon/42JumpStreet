# Stage 03: Backend Core API and Pipeline

## Goal
Expose scanning through the API with a fast path (answer in a fraction of a second from cache and cheap analysis) and a slow path (queued deep scan), orchestrated by one pipeline.

## Depends on
Stages 00-02.

## Components and their single jobs
| Component | Job | Location |
|---|---|---|
| App entry | Create the app, mount routers, load models at startup | `app/main.py` |
| Settings | Load environment configuration | `core/config.py` |
| Error handling | One error shape across the API | `core/errors.py` |
| Logging | Structured logs, hostnames only | `core/logging.py` |
| Rate limiter | Protect scan and check endpoints | `core/rate_limit.py` |
| DB session and models | Persist scans and domain intel | `db/`, `db/models/scan.py`, `domain_intel.py` |
| Scan repository | Save and fetch scan records | `repositories/scan_repo.py` |
| Scan service | Create scans, track state, return results | `services/scan_service.py` |
| 🟨 Check service **[EXTENSION - DEFERRED]** | Fast-path verdict with cache lookup and a time limit | `services/check_service.py` (stub only) |
| Pipeline | Choose analyzers, run in parallel with timeouts, collect results | `engine/pipeline.py` |
| Worker app | Celery configuration | `workers/celery_app.py` |
| Scan tasks | Run the deep scan in the background | `workers/tasks/scan_tasks.py` |
| Verdict cache | Redis cache by host with TTL (safe long, suspicious short) | inside `check_service` using Redis settings |
| Endpoints | `health`, `scan` (submit/get); 🟨 `check` (deferred) | `api/v1/endpoints/` |

## Behavior to implement
1. **Submit scan:** normalize the URL, return the cached result if fresh, else create a scan record and queue a job. Return a scan ID immediately.
2. **Get scan:** return state (`queued`, `running`, `complete`, `failed`) and, when complete, score, band, reasons, evidence summary.
3. 🟨 **[EXTENSION - DEFERRED] Check (extension fast path)**: do not build now; keep the design for later. The verdict cache above is still built, because scans and discovery use it.
   - cache hit -> answer at once;
   - miss -> run the fast model with cached domain intel within a time budget;
   - if the result is uncertain or the domain is new -> return `pending` plus a scan ID and queue a deep scan.
4. **Deduplicate:** one in-flight scan per host, shared by all callers.
5. **Pipeline timeouts:** each analyzer has its own limit; the pipeline returns partial results with a lower confidence instead of failing.
6. **Failure policy:** unknown sites fail open (`pending` / `allow` with low confidence); only confirmed-bad hosts return `block`.
7. **Privacy:** log hostname and result, never form contents or full query strings.

## Tasks
1. Implement settings, error handling, logging, database session and the scan/domain-intel tables with a migration.
2. Implement the scan repository, scan service and the `scan` endpoints.
3. Implement the pipeline with parallel analyzer execution and per-analyzer timeouts.
4. Add Celery worker, Redis wiring and the scan task.
5. 🟨 **[EXTENSION - DEFERRED]** ~~Implement the check service and `check` endpoint with caching.~~ Implement the Redis verdict cache for `scan` only.
6. Add rate limiting and a request-size limit.
7. Write integration tests: submit URL -> poll -> complete; cache hit; timeout produces partial result.
8. Update `docs/api-contract.md` with real request/response shapes.
9. Add `worker` and `beat` to docker-compose.

## Interfaces (names only)
- `POST /api/v1/scan`, `GET /api/v1/scan/{id}`
- 🟨 `POST /api/v1/check` **[EXTENSION - DEFERRED]**
- `GET /api/v1/health`
- Response fields: `verdict`, `score`, `band`, `confidence`, `reasons`, `scan_id`, `ttl`.

## Done when
- A URL submitted through the API completes with a score and reasons.
- A repeated scan of the same host is answered from cache at a noticeably lower latency; measure and record the numbers. (🟨 The same check through `/check` is deferred with the extension.)
- A slow or failing analyzer yields a partial result, not an error.
- The test suite for the API passes in docker-compose.

## Risks and cut-lines
- Blocking calls inside async endpoints: keep slow work in workers.
- Cache poisoning/staleness: short TTL for suspicious, include a "re-check" path.
- Cut-line: skip rate limiting details and `beat` scheduling until stage 08.

## Time estimate
About 4-5 hours.
