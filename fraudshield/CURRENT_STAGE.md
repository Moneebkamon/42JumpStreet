# FraudShield: current stage

> Handoff file. **Updated at the end of every build step.** Read this first when resuming.
> Last updated: 2026-11-23 (day 2, evening: matcher noise fix, scroll boxes, brand-domain check; see the last Update sections). After stage 08, the threat-feed loader, OpenPhish + ready-model download, and stage 03 (stored scans).
> Playbook (the plan): `../FraudShield_playbook/`. Markers there: 🟨 extension deferred, 🟥 out of scope.

## Where we are
Between playbook stages 01 and 03, plus a first version of stage 08. The scanner works end to end (link -> score ->
reasons), including an optional deep scan. Proactive discovery works from a SIMULATED certificate sample: prefilter,
auto-score, SQLite store, `/feed`, `/stats`, `/console` page, Telegram alert code (untested live), cache pre-warm.

| Stage | Status (re-checked 2026-11-23, end of day 2) |
|---|---|
| 00 Initialization | Mostly done: README, Docker files (built and run), sandbox doc. **Empty:** CI workflow, `docs/{architecture,scoring-spec,evidence-handling,privacy-design,demo-script,pitch,performance,api-contract}.md` |
| 01 Data and features | Partly: analyzers, brand matcher, domain lookups, threat feeds (OpenPhish 300 URLs). **Missing:** labeled dataset, feature table, URLhaus/PhishTank |
| 02 Scoring engine | Rules done + ready URL model wired in as a weak signal. **Missing:** calibrated weights, cost-based OR blend, golden test set |
| 03 Backend API/pipeline | Stored scans, history, feedback done (stdlib sqlite). **Missing:** queue/workers, Redis cache, rate limit on /scan, Postgres (all `db/models/*` are empty) |
| 04 Sandbox | Safe browser live-tested (7/7) and verified inside a hardened container. **Missing:** screenshots, cloaking, logo match, browser pool, separate sandbox container, egress filtering |
| 05 Frontend scanner | Done and browser-tested (scanner, deep-scan toggle, recent scans, detail, verdicts) |
| 06 Accounts/auth | Staff login + analyst/admin roles done. **Missing:** public user accounts, user management page (device pairing deferred) |
| 07 Extension | Deferred |
| 08 Proactive discovery | Replay only on a SIMULATED sample. **Missing:** live certificate stream, workers/beat, re-scans, deep scan of flagged domains |
| 09 Analyst console | Done and browser-tested: cases, enforced status flow, frozen evidence + verify, drafts, audit, queue, citizen reports. **Missing:** screenshots/HTML in evidence, takedown actions tracking beyond drafts |
| 10 Maps and search | Not started (`discovery/maps_checker.py`, `search_monitor.py`, map page are empty) |
| 11 Clustering, explanations, alerts | Explanations done (template-based, no LLM). Telegram alert code exists (never sent live). **Not started:** clustering, campaign graph |
| 12 Admin and localization | Done: scoring editor (preview, reason, history), false-positive queue + allowlist. **Missing:** brand editor, user management, Arabic/i18n |
| 13 Testing, demo, pitch | Mostly: 181 tests, README, golden set + report, latency numbers, demo script, pitch notes. **Missing:** backup video, rehearsal, failure drills, fresh-clone test |

## What works today
- `POST /api/v1/scan {"url": "...", "deep": false}` returns score, band, action, confidence, reasons, features,
  and (deep only) a `page` section.
- URL analyzers: normalizer, lexical, homoglyph/punycode, shorteners. Brand matcher for 17 UAE brands
  (`config/brands.yaml`), including leet digits and one-letter typos.
- Domain lookups: RDAP age, DNS, TLS (certifi-verified), cached, "unknown" on failure, skipped for official domains.
- Deep scan (sandbox): headless Chromium via Playwright; public addresses only (guard blocks private/internal,
  records `blocked_hosts`); no downloads, no form submission. Content analyzers: forms (credential, payment,
  cross-domain), pressure and profit language (EN/AR), hidden frames/obfuscated scripts, phones/wallets/handles,
  redirect chain, brand claimed by the page.
- Threat feeds: parsers for OpenPhish, URLhaus, PhishTank; local store `data/interim/threat_feeds.db`; the `threat_intel`
  analyzer sets `threat_listed` (exact URL, or whole host except on shared hosting like github.io), which triggers the
  existing override (score floored at 85). With no database loaded it quietly answers "not listed".
  `scripts/fetch_feeds.py` loads a file you downloaded (`--file SOURCE PATH`) or downloads (`--download ... --yes`; without
  `--yes` it only prints the plan). Download results 2026-11-23: OpenPhish OK (300 URLs, 269 hosts, ~half on shared hosting so only exact-URL matches count); URLhaus FAILED with 410 Gone (abuse.ch retired `/downloads/csv_online/`; find its current download or API, likely needs an Auth-Key); PhishTank not tried (needs a key).
- Triage (OR, first piece): `engine/prioritizer.py` + `GET /api/v1/triage?budget_seconds=60` rank discovered domains for a
  closer look under a time budget (value = harm weight x suspicion x informativeness; greedy by value per second).
  RECOMMENDS ONLY, never fetches. Weights are hand-set.
- Stored scans: `repositories/scan_repo.py` (stdlib sqlite3, `data/interim/fraudshield.db`, env `FRAUDSHIELD_DB`). Every scan is saved
  (a storage failure never breaks a scan). Analyst/user verdicts (`scam`/`safe`) are saved on the scan: these are future labels.
  Front end: `/scan` history (polls 10 s), `/scan/[scanId]` detail with the verdict buttons, links from the scanner and home page.
- Rules: 16 rules with weights in `config/rule_weights.yaml`. Bands in `config/risk_bands.yaml`.
- Frontend: scanner at `/` with gauge, verdict, reasons, domain facts, page section, deep-scan checkbox, 404/error pages.
- Discovery (stage 08): `scripts/run_discovery.py` replays `data/samples/ct_stream.jsonl` (986 SIMULATED events) through the
  prefilter (brand, homoglyph, keyword+risky TLD, keyword+hyphens), scores survivors URL-only, stores them in
  `data/interim/discovery.db`. `GET /api/v1/feed`, `GET /api/v1/stats`; UI at http://localhost:3000/console (polls every 5 s).
  A scanned bare-domain link that discovery already scored is answered from the DB with `cached: true`.
  Measured figures and caveats: `docs/discovery.md`.
- Tests: **132 backend tests pass** (offline, mocked; 7 live sandbox tests are skipped unless enabled). **7 live sandbox tests pass** when run with the env vars below.

## How to run (Windows, from `fraudshield/`)
- First time on a new machine: `yarn setup:backend` (creates `backend/.venv`; also run
  `backend/.venv/Scripts/python -m playwright install chromium` for the deep scan).
- `yarn backend` (port 8000), `yarn frontend` (port 3000, proxies `/api/v1/*` to the backend). Open http://localhost:3000.
- `yarn test` runs the offline suite.
- Discovery demo: `backend/.venv/Scripts/python scripts/run_discovery.py --reset` (short-lived, writes the SQLite file, prints
  figures), then start backend + frontend and open `/console`. Telegram alerts only fire if `TELEGRAM_BOT_TOKEN` and
  `TELEGRAM_CHAT_ID` are set; the output marks simulated data `[SIMULATED]`.
- Live browser tests (launches Chromium, serves staged pages from a short-lived local server inside the test):
  `cd backend && FRAUDSHIELD_LIVE=1 FRAUDSHIELD_SANDBOX_ALLOW_HOSTS=127.0.0.1 .venv/Scripts/python -m pytest tests/integration -s`
- Env switches: `FRAUDSHIELD_NETWORK=0` disables RDAP/DNS/TLS (tests set it). `FRAUDSHIELD_SANDBOX_ALLOW_HOSTS`
  lets the sandbox reach listed private hosts (demos/tests only, **never in production**).

## Known issues and limits
- **Sandbox is not container-isolated yet.** It is a headless browser on the host. The address guard blocks
  internal targets, but there is no network egress rule, so DNS rebinding is a known gap and a hostile page
  still executes in a local browser. `infra/docker/sandbox.Dockerfile` is empty. Do this before pointing it at live scams at scale.
- **Weights are guesses.** All rule points and TLD risks are my starting values; nothing is calibrated on data.
- **No labeled data / no measured accuracy yet.** Do not quote accuracy numbers.
- **False positives by design at URL-only level:** e.g. a legitimate `.ae` site with "emirates" in its name scores 35.
  A page that merely mentions a brand in its title counts as a brand claim (only scores with a credential form).
- RDAP coverage for `.ae` / `.abudhabi` is untested; the age rule may not fire for them.
- `brands.yaml` official domains: checked by web search 2026-11-23, see `docs/brand-domain-verification.md`. Still **unconfirmed**: `tamm.abudhabi`, `salik.gov.ae` (real site may be `salik.ae`), whether `adcb.ae` is owned, and `microsoft-int.com` (added from memory). A person should confirm these.
- Deep scan launches a fresh browser each time (~4-5 s per page). No browser pool.
- 20 empty route placeholder `page.tsx` files make `tsc`/`next build` fail (dev is fine). They clear as pages get built.
- Scanner UI has never been looked at in a browser (Chrome extension was not connected). Verified only by tsc, eslint and curl through the proxy.
- Scans are not persisted; `scan_id` is random and cannot be fetched later.
- **Discovery uses a simulated sample**, so pass-through and recall figures describe the code on planted data only. The live
  stream source is a stub (`live_source` raises). Issue-to-detection time is meaningless in replay (shown as simulated).
- Brand matcher gap: digit `1` is read as `l` only, so `ad1b`/`em1ratesid` (1 for i) are missed (2 of 49 planted lookalikes).
- **SQLAlchemy cannot be imported on this machine** (Windows Application Control blocks its compiled `_immutabledict_cy`; the pure-Python
  switch did not help). So all storage uses stdlib `sqlite3` behind small repo modules (`scan_repo.py`, `domain_watch.py`,
  `feed_loader.py`). Three separate SQLite files for now (`fraudshield.db`, `discovery.db`, `threat_feeds.db`); merging them and any
  Postgres move is a rewrite of those repo modules. Do not try to bypass the policy.
- Keyword-only and homoglyph-only candidates score "safe" at URL level (15 / 25); they need a deep scan to be judged.
- Telegram sending is tested with mocks only; it has never sent a real message.
- Next 16 differences: `middleware.ts` is `proxy.ts`; `error.tsx` takes `retry`; empty special files crash the dev server.

## Agreed order for what is left (user confirmed: 08 first; then hybrid rules + OR + ML)
Direction decided 2026-11-23: keep the explainable rules, add a small ML model for new patterns, and an OR layer that
blends the scores, sets cost-based thresholds and prioritises the deep-scan queue under a budget.
0. **DONE 2026-11-23, decision: use a ready model instead of training our own (for now).** Downloaded
   `CrabInHoney/urlbert-tiny-v2-phishing-classifier` (MIT, 15 MB safetensors, hash verified) to `ml/artifacts/urlbert-tiny-v2/`
   and the Tranco top-1M list to `data/raw/tranco/` (benign set). NOT yet run: the venv has no torch/transformers; installing
   them was approved and DONE (separate `ml/.venv`; torch 2.15 CPU). `transformers` cannot load (its `regex` dep is blocked by
   Application Control), so `ml/tiny_bert.py` runs the model in plain torch. Caveats: the model is
   URL-text only, global (not UAE), self-reported val 0.9622 on its own data (trained on `ealvaradob/phishing-dataset` urls.json,
   so do NOT test on that set); a newer v3 exists. Honest test set: OpenPhish (fresh positives) vs a Tranco sample (negatives),
   remembering Tranco negatives are easy (popular sites), so results will look better than real life. Use it only as one extra
   score in the blend if it adds value over the rules.
0b. **First check done (see `docs/ready-model-eval.md`)**: on 300 OpenPhish URLs vs 400 Tranco domains the model gets AUC 0.90
   (63% of phish at 5% false alarms; feed it the URL WITHOUT the scheme), the rules get AUC 0.51 (289/300 score 0; they are UAE-brand
   focused and the run was offline). Model has a TLD bias (.ru/.cn false alarms). Verdict: keep as ONE extra signal, not a decider.
   WIRED IN (same day): `backend/app/ml/` runs it in numpy (numpy/safetensors/tokenizers installed in the backend venv; matches the torch
   reference within 1e-6, tested), analyzer `url_model`, rules `ml_url_pattern_strong` (+15, p>=0.95) and `ml_url_pattern` (+8, 0.83-0.95).
   Optional: `FRAUDSHIELD_ML=0` or missing files turn it off. Tests run with it off except `test_ml_model.py`. Measured effect: it adds
   a reason and a few points, but alone it never reaches "suspicious" (0-1% of held-out phish score >= 30). Raising weights is a pending
   decision (more phish caught vs more false alarms and TLD bias): wait for UAE data and network signals. See `ml/README.md`.
1. **More threat data** (OpenPhish only so far: 300 URLs is far too few to train on; need URLhaus/PhishTank via keys or files) plus a benign set
   (popular domains and the official brand domains). Without labeled data nothing below can be calibrated.
   Do NOT train on `data/samples/ct_stream.jsonl` (it is simulated).
2. **Feature table and a small model** (tree or logistic first); held-out evaluation before quoting any figure. Playbook stage 01/02.
3. **OR layer:** fit blend weights and band cutoffs by expected cost (a miss costs more than a false alarm);
   scan-budget prioritisation for discovery (works without labels, can be built any time).
4. **Stage 03: stored scans** (real DB replaces the discovery SQLite, `GET /scan/{id}`, history page, analyst feedback as labels).
5. **Sandbox in Docker** (restricted egress). Needed before deep-scanning real scam sites at scale.
6. **Stage 09: analyst console.**
Smaller, any time: finish stage 08 (live stream, re-scans, deep scan of flagged domains), fix the `1`-for-`i` matcher gap,
staged demo server script, screenshots in the sandbox, README, fill or remove the 20 empty page placeholders.
Claims to avoid: "detects unknown scams" (feeds are biased to already-caught scams); say "adapts as new labeled cases arrive".

## Rules of engagement (from the user)
- **Standing go-ahead (2026-11-23):** build stage by stage without asking at each step. Still stop for: downloads, servers/background
  processes, external sends/keys, accuracy-affecting choices (show numbers first), and a browser look at the UI.
- **Never fetch/open/deep-scan a real scam or suspected-scam URL without the user's explicit permission.** Feed lists and
  discovered domains are data to parse/score only. Local staged pages (`data/samples/staged`) are fine.
- **Never start a server or background process, or download anything large, without saying so first and getting a yes.**
- Static checks (mocked pytest, tsc, eslint) are fine to run.
- Update this file at the end of every build step.

## Update log
- 2026-11-22: scaffold, config, URL analyzers, brand matcher, rules engine, `/scan`, domain intel, scanner page,
  sandbox + content analyzers + live test, deep-scan toggle.
- 2026-11-23: stage 08: sample generator, prefilter, replay/reconnect/rate-cap listener, ingest, SQLite store, `/feed`, `/stats`,
  Telegram alert code, cache pre-warm, `/console` page, `docs/discovery.md`. Needs your eyes in a browser (never viewed rendered).
- 2026-11-23: threat-feed parsers, store, lookup (`threat_intel` analyzer), `fetch_feeds.py` (dry-run by default). No feed downloaded.
- 2026-11-23: scan-budget prioritizer + `/triage` (recommend-only). Standing go-ahead and the no-real-scam-URLs rule recorded.
- 2026-11-23: ran `fetch_feeds.py --download openphish urlhaus --yes` (user approved): OpenPhish loaded 300 URLs, URLhaus 410 Gone. Override verified on a loaded URL (score 85).
- 2026-11-23: user chose a ready model. Downloaded urlbert-tiny-v2 (hash ok) + Tranco top-1M. Awaiting yes to install torch/transformers in an ML venv.
- 2026-11-23: stage 03 storage: scan_repo, `/scans`, `/scan/{id}`, feedback endpoint, history + detail pages. 126 tests pass, tsc/eslint clean. Not yet viewed in a browser.
- 2026-11-23: ML venv installed, `ml/` eval scripts + `tiny_bert.py`, first held-out comparison documented. Servers (ports 8000/3000) left running for the user to test.
- 2026-11-23: servers stopped (ports 8000/3000 verified free). Ready model wired into the scorer (numpy), parity-tested vs torch, held-out effect documented.

### Update: stage 09 built (analyst console), not yet browser-verified
- Backend: cases with enforced status flow (reason required), SHA-256 frozen evidence + verify, audit log, takedown drafts (draft/export only, never sent), citizen reports (honeypot + rate limit), triage queue. 14 new tests; full suite 146 passed, 7 skipped.
- Frontend: shared navbar/footer, case list + detail, queue, report form `/report`, audit `/admin/audit`, "Open case" buttons on feed rows and scan detail; all former empty files filled. `tsc`, `eslint` and `next build` pass (24 routes).
- NOT done: running both servers and driving the UI end to end (the tool permission for starting servers was denied in this session). Script ready: scratchpad `e2e.py` (Playwright, localhost only, example.com domains).
- Caveat: no login yet; X-Actor header is only an audit label.

### Update: stage 09 browser-verified
- Playwright (localhost only, example.com domains) drove scan → saved result → verdict → case → evidence freeze + verify → draft → note → status → cases list → queue → report → audit → stub pages → phone width (no overflow). All passed. Screenshots: `data/interim/shots/`.
- UI: added urlscan-style "Recent scans" table on the home page.

### Update: login, Docker files, README
- Login: scrypt passwords, signed HttpOnly session cookie (8 h), roles analyst/admin, login rate limit (10/5 min), failed logins audited. Auth is ON by default (`FRAUDSHIELD_AUTH=0` disables; tests do). Staff routes need analyst; audit log needs admin. Actor in the audit log now comes from the session, not the X-Actor header. Create users: `python scripts/create_user.py <name> <analyst|admin> --generate` (password goes to `data/interim/credentials-<name>.txt`, git-ignored).
- Front end: `/login`, navbar shows session, staff pages guarded (`RequireStaff`), "Open a case" only for signed-in staff. Public: scan, recent scans (visible to everyone, urlscan-style), report.
- Tests: 154 passed, 7 skipped. Browser run passed with login and roles.
- Docker: Dockerfiles and compose written, `docker compose config` validates; NOT built or run (several GB download needs a yes). See `docs/sandbox.md`.
- README written with a demo path.
- Known: scans list is public; sessions cannot be revoked server-side; no user-management page; dev backend is run without `--reload` (reload hung on multi-file edits).
- Live sandbox tests: 7/7 passed against local staged pages (no real URLs, no download needed). Private-address guard verified: 10.0.0.5 and 169.254.169.254 blocked.

### Update: Docker stack built and verified
- `docker compose build` + `up -d` works (backend 3.8 GB with Chromium, frontend 1.1 GB). Full browser flow passes against it (login, roles, scan, case, evidence, draft, report, audit, phone width).
- Bugs the container test found and fixed: frontend port was unreachable (Docker cannot publish from an `internal` network -> added `web` network); Playwright unpinned vs image browsers (pinned 1.65.2 in requirements and Dockerfiles); config/model paths assumed the repo layout (added FRAUDSHIELD_CONFIG_DIR and FRAUDSHIELD_MODEL_DIR to the image).
- Hardening verified inside the container: uid 10001, read-only root fs, zero capabilities, deep-scan browser works and blocks 169.254.169.254.
- Still open: browser shares the API container; no destination-level egress filtering; the in-container feed/threat DBs start empty (no sample data baked in); worker.Dockerfile untested.
- Stack is left running (frontend :3000, backend :8000). Stop with `docker compose down`.

### Update: plain-language explanations (stage 11, first piece)
- `engine/explainer/` (selector + fixed templates, no LLM): every scan result has `explanation`, 2-4 sentences built only from rules that fired or recorded overrides, band-aware opening, honest caveats (checks that failed, page not opened, model-only signal). Old stored scans get one filled in on read. Shown on the result card. `llm_client.py` stays an empty reserved slot.
- Tests: 162 passed, 7 skipped. Verified in the Docker stack through the browser.
- Data note: the sample `adcb.ae` link scores 43 because only `adcb.com` is listed; ownership of `adcb.ae` is unconfirmed (see `docs/brand-domain-verification.md`).

### Update: admin tuning, false-positive review, golden set, docs
- Scoring editor (`/admin/rules`, API `/admin/settings`): rule points (0-60) and band cutoffs stored over the YAML defaults, effective immediately, preview re-scores stored scans, reason required, append-only history + audit. Browser-verified (score 65 -> 35 -> 65).
- False-positive review (`/admin/feedback`, `/admin/allowlist`): "safe" reports on flagged links -> admin promotes the domain to an allowlist or dismisses. Allowlist caps the score at 10; a threat-feed hit still wins; shared-hosting domains and threat-listed domains cannot be allowlisted. Browser-verified (High risk -> Looks safe -> removed -> High risk).
- Golden set: `backend/tests/fixtures/golden_urls.json` (32 hand-labelled links), `scripts/run_golden.py`, `docs/golden-report.md`: rules flag 13/14 phish-style links, 1/18 false alarm; with the URL model 2/18 (model adds a false alarm). Regression test `test_golden.py`. Development check only.
- Measured: scan median 103 ms (new link), 43 ms (repeat), ~1 s for first lookup of a new domain, deep scan ~0.94 s on a local page. See `docs/performance.md`. (`localhost` on Windows adds ~2 s; use 127.0.0.1.)
- Docs written: `performance.md`, `demo-script.md`, `pitch.md`, `golden-report.md`. Still empty: `architecture.md`, `scoring-spec.md`, `evidence-handling.md`, `privacy-design.md`, `api-contract.md`, CI workflow.
- Tests: 181 passed, 7 skipped.

### Update: Docker feed seeding
- The Docker image now carries the SIMULATED certificate sample and `run_discovery.py`; seed with `docker compose exec backend python scripts/run_discovery.py --sample /srv/samples/ct_stream.jsonl --reset` (Git Bash: prefix `MSYS_NO_PATHCONV=1`). Verified: queue and feed show 100+ rows in the signed-in console.
- Triage queue now says the detections are simulated.

### Update: demo-build safety decisions
- Decision: NO deep scan of real scam pages; this is a demo build. Deep scan is staff-only (401 for visitors), 5/min per user; `/scan` 60/min per client (`FRAUDSHIELD_RATE_LIMIT=0` disables, tests do). Scanner UI shows the safe-browser option only to signed-in staff, with a "staged pages only" warning; footer says demo build.
- Sandbox gaps (docs/sandbox.md) stay open: separate sandbox container, outbound proxy, Chromium sandbox. Planned order if resumed: fetcher seam + static fetcher (can only add suspicion), separate sandbox service + proxy, labelled-link evaluation.
- Later (user asked to keep for after sandbox): bulk ingest endpoint with service token, live certificate stream (needs yes), daily OpenPhish refresh.
- Tests: 186 passed, 7 skipped.

### Update: real-data evaluation (MVP gap 2) - important finding
- `scripts/run_real_eval.py` scores 300 real OpenPhish URLs vs 300 sampled Tranco home pages, text only, feed rule off. Reports: `docs/real-data-eval.md` (rules) and `docs/real-data-eval-ml.md` (+model).
- Result: rules catch 0/300 real phishing at the suspicious cutoff (model: 2/300); 0 false alarms. The golden-set numbers do NOT generalise. Most real URLs are random names on free hosting, brand look-alikes outside our brand list, or shorteners.
- MVP implication: detection must lean on feeds + domain/cert signals + page analysis; add free-hosting/random-label rule and wider brand list using a train/test split; measuring network signals on real URLs needs the user's yes (contacts domains).
- Still open for MVP gap 1: live certificate stream (needs user's yes; stoppable container planned).

### Update: MVP step 1 - rules + brands on real data (measured)
- New: `analyzers/url_analyzer/hosting.py` (free-hosting generated-name rule +30; popular-domain flag from `config/popular_domains.txt`, Tranco top 5000), 18 global brands with explicit tokens in `config/brands.yaml`, `tokens`/`exact_only` options in the brand registry (fixes `eand` false alarms like timeanddate.com).
- Real-data result (held-out half of 300 OpenPhish URLs, text only, feed rule off): ~57% reach 'suspicious' (train half 62%), ~0.8% false alarms on 1000 sites ranked 5001-50000, 0% reach 'high risk'. Details + limits: `docs/real-data-findings.md`, `docs/real-data-eval*.md`. Golden set unchanged (13/14, 1/18). Tests 186 passed.
- Next (user approved all, 2026-11-23): live CT reader as stoppable container (check which stream is up first, tell user before connecting), then low-contact network signals (registry age, CT-log certs, public-resolver DNS, NO TLS handshake) on the same 300 URLs.

### Update: live certificate stream (MVP step 2) - working, precision is poor
- Self-hosted `certstream-server-go` (image pinned by digest, v1.10.1) + `ct-listener`, both under compose profile `live` (OFF by default): `docker compose --profile live up -d certstream ct-listener`; stop: `docker compose --profile live stop certstream ct-listener`. Config: `infra/certstream/config.yaml` (Google's logs only). Hardened: read-only, no capabilities, own internal network, nothing published to the host.
- Measured: all operators ~10 MB/s (too heavy); Google only ~0.9 MB/s (~3 GB/hour, ~77 GB/day), ~500 certificates/s, certstream ~33 MB RAM. Listener: URL model OFF + 1 CPU cap (the model cost ~2.5 cores at this volume); prefilter sped up 6x (linear one-edit check, identical results on 200k random pairs).
- Dashboard: live status line (heartbeat), and a fixed-height scrollable "Recently checked domains" panel (last 300 of a 1000-row ring buffer) on /console and /console/monitoring. API `GET /api/v1/checked`.
- Live result (first ~100k certificates): 2.6% pass the name check; of 200 live detections 121 reach 'suspicious' and most look like false alarms (microsoft-int.com internal hosts, `adcb` inside random strings, French 'du', 'fab' in CDN test names, brand words on free hosting). **Precision on the live stream is poor; not measured formally.** Next: require stronger evidence for short tokens inside long random labels, add vendor-owned domains (microsoft-int.com...), tune on a labelled sample.
- Also fixed: Docker backend health check now uses /api/v1/health (was /queue, which needs login -> never healthy). Tests: 192 passed, 7 skipped.

### Update: live-stream false alarms cut (matcher) + scroll boxes
- Matcher (`name_matcher.py`, `brands.yaml`, `registry.py`): brand name inside a long junk label is ignored (label may exceed the token by at most 14 chars); tokens under 6 chars must sit at the start or end of a label; tokens under 4 chars (moi, du, fab, dib) match only in the registered domain, not subdomains; per-brand `ignore_words` (finance != binance, tammy != tamm); `microsoft-int.com` added as Microsoft-owned (verify).
- Measured by replaying the 2,135 stored LIVE detections (copied from the container DB): 'suspicious' 1,384 -> 145, 'high risk' 6 -> 2; real lookalikes kept (padpal.ai, fabebook.com, metamsk-login-docs, microsogt.com, 9oogle.org, rnicrosoft). Real OpenPhish check (text only): suspicious+ 59.3% -> 58.7%, false alarms unchanged (0.8%). Limit 10 gave 56.7%, so 14 was chosen. This is a tuning check on the same live sample, NOT a held-out precision figure.
- Still noisy: `netflix.com.mcas.ms` and `microsoft-falcon.net` (likely Microsoft-run, unverified so not allowlisted), whatsapp/telegram/instagram as a subdomain on unrelated sites, `*.chatgpt.site` generated names, `tammco.sa`. Legit IDN domains (xn--..., German/Nordic/Russian) are kept for punycode but score safe.
- 12 new tests in `tests/unit/test_brand_noise.py`.
- Frontend: every table (feed, cases, queue, recent scans, audit, rules) and the `/scan` history list now scroll (`max-h-96`, sticky headers). Not yet viewed in a browser.

### Update: brand domains checked + what is next (handoff)
- Web-search check of official domains: `docs/brand-domain-verification.md`. Confirmed: adcb.com, bankfab.com, emiratesnbd.com, adib.ae, adpolice.gov.ae, icp.gov.ae, etisalat.ae, eand.com. Unconfirmed (need a person): tamm.abudhabi, salik.gov.ae, adcb.ae ownership, microsoft-int.com. `mcas.ms` is a Microsoft proxy suffix but is deliberately NOT allowlisted (others' traffic uses it). `brands.yaml` was not changed in this step.
- Docker stack was rebuilt (frontend + backend) and is RUNNING on :3000/:8000 with the new scroll boxes and matcher. The user confirmed the scroll boxes look right in the browser. Live reader containers (`--profile live`) are stopped.
- Login note: `data/interim/credentials-docker.txt` password for `admin1` was REJECTED by the rebuilt stack (volume password differs). To get in, make a new account: `docker compose exec backend python scripts/create_user.py <name> admin --generate` (file is written inside the container, so copy it out or set a password interactively). Do not guess passwords.
- Next, in order: (1) person confirms the unconfirmed domains above; (2) low-contact network signals (registry age, CT-log certs, public-resolver DNS, NO TLS handshake) on the 300 OpenPhish URLs, user approved, tell them before any contact, held-out split; (3) hand-label the ~145 remaining live 'suspicious' domains to get a real precision number (replay script idea: copy `/data/discovery.db` out of the container with `docker compose cp`, replay through `prefilter` + `run_pipeline(use_network=False)`); (4) fill empty docs + CI workflow (`architecture`, `scoring-spec`, `evidence-handling`, `privacy-design`, `api-contract`); (5) separate sandbox container + proxy, URLhaus fix, Arabic.

### Note: how the ML pieces fit together (read this if `ml/` confuses you)
- There is ONE model: the downloaded `urlbert-tiny-v2` (MIT, URL text only, global, not UAE). We did NOT train our own; no labelled UAE data exists yet.
- Used by the scanner: `backend/app/ml/` (`model_loader.py`, `predictor.py`) runs it in numpy. It is one weak signal: rules `ml_url_pattern_strong` (+15) and `ml_url_pattern` (+8). It never reaches "suspicious" alone. The Docker image copies `ml/artifacts/` to `/srv/ml/artifacts` (env `FRAUDSHIELD_MODEL_DIR`). Off with `FRAUDSHIELD_ML=0`. The live certificate listener runs with it OFF (too CPU-heavy at ~500 certs/s).
- `ml/` is the lab bench, not a second model: `artifacts/` (the model files), `tiny_bert.py` + `score_with_model.py` (plain-torch reference, used only to check numpy parity), `build_eval_set.py` + `report.py` (evaluation on OpenPhish vs Tranco; results in `docs/ready-model-eval.md`), `.venv` (torch, ~950 MB, only for those scripts; safe to delete if disk is needed, the app does not use it).
- Empty placeholders kept for a possible future own model: `ml/src/`, `ml/notebooks/`, `ml/reports/`, `backend/app/ml/shap_explainer.py`.
- See also `ml/README.md`.

### Update: official-domain facts + hydration warning
- Scanner change (`engine/feature_assembler.py`): the age/DNS/certificate lookups now ALSO run for official domains (they were skipped, so a real brand domain showed only "Domain is an official domain of X" with no facts). The score cap and the "official" verdict are unchanged; only the page fetch is still skipped for official domains. Test `test_official_domain_shows_lookups_but_stays_safe` replaces `test_official_domain_skips_network`. 204 passed, 7 skipped. NOT yet rebuilt into Docker or checked in a browser. Cost: about 1 s extra on the first lookup of an official domain (cached afterwards).
- Why the user saw only the official note: the global brands (Microsoft, Google...) were added to `brands.yaml` after their first test, so their domains became official and were skipped.
- A React "hydration mismatch" warning was reported (pasted without the diff, page unknown). Searched the app: nothing rendered on the server uses time, random, window or locale (all of that is behind loaded data). Most likely a browser extension changing `<html>`/`<body>`. Added `suppressHydrationWarning` to those two tags in `app/layout.tsx`. If it still appears, get the "+ / -" lines from the console message and the page URL; that names the real component.

### Update: shared demo password (CHANGE BEFORE ANY REAL USE)
- 2026-11-23, at the user's request: ALL existing accounts (`admin1` admin, `analyst1` analyst) were set to one shared, weak demo password, in both the local DB (`data/interim/fraudshield.db`) and the Docker volume. Ask the project owner for it; it is deliberately not written here. The `data/interim/credentials-*.txt` files are now STALE and do not work.
- Replace it before anyone else can reach the app: `python scripts/create_user.py <name> <analyst|admin>` (asks for the password, hidden). Login rate limit is still 10 failures per 5 minutes.

### Update: browser extension added and connected (stage 07 first version, NOT tested in Chrome)
- A teammate's Chrome MV3 extension (repo-root `extension/`, committed in git) was COPIED into `fraudshield/extension/` (the root copy was left untouched; decide which one is canonical). It scores Google Search/Maps links locally (67 tests pass).
- Connected: gray-zone (`medium`) links call `POST /api/v1/scan` (URL only) via the `llmAnalyze` hook, final = max(local, backend), backend reasons appended in English; popup "report" button posts to `/api/v1/citizen-reports`. API base default `http://127.0.0.1:3000` (override `fe:api-base` in extension storage). Manifest got host permissions for ports 3000/8000.
- Not done: load in Chrome and try against the running stack (stack was not running at the time), Arabic text for backend reasons, aligning score scales, README/pitch privacy wording, `docs`/CI mention. The scan rate limit (60/min per client) applies to the extension.
