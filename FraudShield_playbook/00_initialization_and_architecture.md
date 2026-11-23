# Stage 00: Initialization and Architectural Layout

## Goal
Create the repository, the complete directory structure, the component map and the conventions, so every later stage drops files into a place that already exists. No feature logic yet.

## Depends on
Nothing.

## Scope status (current decision)
- 🟨 **[EXTENSION - DEFERRED]:** the browser extension is not executed for now. Create the `extension/` folder as an empty stub only, and keep the backend pieces marked 🟨 below as stubs (empty files, no logic). Nothing is deleted, so the work can resume later.
- 🟥 **[OUT OF SCOPE]:** `visual_match` embeddings, `partners`/`partner_key`, `webhook` alerts.
- Markers inside the tree are written as comments (`# 🟨 ...`, `# 🟥 ...`) because code blocks cannot show highlights.

## 1. Architecture decisions (fixed for the whole project)
| Decision | Choice | Reason |
|---|---|---|
| Repo style | One monorepo (`fraudshield/`) | One clone, one compose file, shared config |
| Frontend | Next.js (App Router, TypeScript), `src/` directory | Standard Next.js structure; route groups per user type |
| Backend | FastAPI (Python 3.11) with layered structure | Standard API / service / repository / model separation |
| Async work | Celery workers + Redis | Slow scans and discovery must not block the API |
| Database | PostgreSQL (SQLite allowed for the first hours only) | Cases, evidence, audit need relations |
| Cache | Redis | Verdict cache and queue |
| Browser sandbox | Playwright in its own Docker image | Isolation from the API |
| 🟨 Extension **[DEFERRED]** | Chrome/Edge Manifest V3, TypeScript | One codebase for both browsers (not built now) |
| ML | scikit-learn / XGBoost, trained in `ml/`, served by the backend | Same feature code for training and serving |
| Shared config | `config/` YAML files read by the backend | Brands, rule weights, risk bands, tuned without code changes |

**Rule against training/serving skew:** feature extraction lives only in `backend/app/analyzers/`. The `ml/` scripts import it; they never re-implement it.

## 2. Repository layout

```
fraudshield/
├── README.md
├── Makefile                          # shortcuts: up, down, test, lint, seed
├── docker-compose.yml                # api, worker, beat, sandbox, db, redis, frontend
├── docker-compose.override.yml       # dev-only overrides (hot reload, ports)
├── .env.example                      # every variable name, no secrets
├── .gitignore
├── .editorconfig
├── .github/
│   └── workflows/ci.yml              # lint + tests on push
│
├── docs/
│   ├── architecture.md               # this layout + diagrams
│   ├── api-contract.md               # endpoint list, request/response shapes
│   ├── scoring-spec.md               # features, rule weights, bands, overrides
│   ├── privacy-design.md             # what is collected, minimization, retention
│   ├── evidence-handling.md          # evidence package fields, hashing, audit
│   └── decisions/                    # short ADR notes, one file per decision
│
├── config/                           # non-secret, human-editable
│   ├── brands.yaml                   # brand registry: names (EN/AR), official domains, keywords
│   ├── allowlist_seed.txt            # top-site domains seed
│   ├── rule_weights.yaml             # rule name -> points
│   ├── risk_bands.yaml               # score ranges, labels, actions
│   └── tld_risk.yaml                 # risky TLD weights
│
├── data/                             # gitignored except samples/ and .gitkeep
│   ├── raw/                          # downloaded feeds, untouched
│   ├── interim/                      # cleaned, deduplicated
│   ├── processed/                    # feature tables used for training
│   └── samples/                      # small committed demo data (staged pages, fixtures)
│
├── ml/                               # training only, never imported by the API
│   ├── README.md
│   ├── notebooks/                    # exploration
│   ├── src/
│   │   ├── build_dataset.py          # merge feeds, dedupe, assign labels
│   │   ├── label_store.py            # read/write labels with source and date
│   │   ├── make_features.py          # call backend analyzers over the dataset
│   │   ├── train.py                  # train fast and full models
│   │   ├── evaluate.py               # time-based split metrics, false-positive report
│   │   ├── calibrate.py              # probability calibration, threshold choice
│   │   └── export_model.py           # write versioned artifact + metadata
│   ├── reports/                      # metric tables, plots
│   └── artifacts/                    # versioned model files (fast_vN, full_vN) + metadata json
│
├── backend/
│   ├── pyproject.toml                # dependencies and tool config
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/                 # migrations
│   ├── app/
│   │   ├── main.py                   # app creation, router mounting, startup hooks
│   │   │
│   │   ├── core/                     # cross-cutting basics
│   │   │   ├── config.py             # settings loaded from env
│   │   │   ├── security.py           # password hashing, token creation/verification
│   │   │   ├── logging.py            # structured logs
│   │   │   ├── rate_limit.py         # per-key / per-IP limits
│   │   │   ├── errors.py             # error types and handlers
│   │   │   └── constants.py          # enums: verdicts, statuses, roles
│   │   │
│   │   ├── api/                      # HTTP layer only: parse, validate, call a service
│   │   │   ├── deps.py               # shared dependencies: db session, current user, device, role guard
│   │   │   └── v1/
│   │   │       ├── router.py
│   │   │       └── endpoints/
│   │   │           ├── health.py
│   │   │           ├── scan.py             # submit URL, get scan result
│   │   │           ├── check.py            # 🟨 EXT-DEFERRED: extension fast-path verdict
│   │   │           ├── auth.py             # register, login, refresh
│   │   │           ├── devices.py          # 🟨 EXT-DEFERRED: extension pairing and tokens
│   │   │           ├── events.py           # 🟨 EXT-DEFERRED: extension event upload, user history
│   │   │           ├── feedback.py         # false-positive reports
│   │   │           ├── blocklist.py        # 🟨 EXT-DEFERRED: compact list for extension (🟥 partners out of scope)
│   │   │           ├── feed.py             # live detections (dashboard)
│   │   │           ├── brands.py           # brand registry admin
│   │   │           ├── allowlist.py        # allowlist admin
│   │   │           ├── cases.py            # analyst cases
│   │   │           ├── evidence.py         # evidence packages
│   │   │           ├── takedowns.py        # takedown report drafts and status
│   │   │           ├── citizen_reports.py  # public report page backend
│   │   │           ├── listings.py         # Maps listing checks
│   │   │           ├── search_monitor.py   # search-result checks
│   │   │           ├── campaigns.py        # clusters
│   │   │           ├── partners.py         # 🟥 OUT OF SCOPE: partner keys and feeds
│   │   │           ├── stats.py            # dashboard numbers
│   │   │           └── admin.py            # thresholds, rules, users
│   │   │
│   │   ├── schemas/                  # request/response shapes, one file per domain
│   │   │   ├── scan.py  check.py  auth.py  device.py  event.py  feedback.py
│   │   │   ├── case.py  evidence.py  takedown.py  citizen_report.py
│   │   │   ├── listing.py  campaign.py  brand.py  partner.py  stats.py
│   │   │
│   │   ├── db/
│   │   │   ├── base.py               # declarative base
│   │   │   ├── session.py            # engine and session factory
│   │   │   ├── init_db.py            # create tables / seed on first run
│   │   │   └── models/               # one table-group per file
│   │   │       ├── user.py  device.py  scan.py  event.py  feedback.py
│   │   │       ├── brand.py  allowlist.py  domain_intel.py
│   │   │       ├── case.py  evidence.py  action.py  citizen_report.py
│   │   │       ├── listing.py  campaign.py  partner_key.py  audit_log.py
│   │   │
│   │   ├── repositories/             # database access only, one per model
│   │   │   ├── user_repo.py  device_repo.py  scan_repo.py  event_repo.py
│   │   │   ├── feedback_repo.py  brand_repo.py  allowlist_repo.py
│   │   │   ├── case_repo.py  evidence_repo.py  action_repo.py
│   │   │   ├── citizen_report_repo.py  listing_repo.py  campaign_repo.py
│   │   │   ├── partner_key_repo.py  audit_repo.py
│   │   │
│   │   ├── services/                 # business logic; calls repositories and engine
│   │   │   ├── scan_service.py       # create scan, orchestrate, return state
│   │   │   ├── check_service.py      # fast-path verdict with cache and timeout
│   │   │   ├── auth_service.py
│   │   │   ├── device_service.py     # 🟨 EXT-DEFERRED: pairing codes, device tokens
│   │   │   ├── history_service.py    # user security history
│   │   │   ├── feedback_service.py   # FP handling, allowlist promotion
│   │   │   ├── blocklist_service.py  # 🟨 EXT-DEFERRED: build compact blocklist
│   │   │   ├── case_service.py       # case lifecycle and status rules
│   │   │   ├── evidence_service.py   # freeze, hash, store, verify evidence
│   │   │   ├── takedown_service.py   # build report drafts (never auto-send)
│   │   │   ├── priority_service.py   # triage priority score
│   │   │   ├── citizen_report_service.py
│   │   │   ├── stats_service.py
│   │   │   └── audit_service.py      # write audit entries
│   │   │
│   │   ├── analyzers/                # each analyzer = one job, returns a feature dict
│   │   │   ├── url_analyzer/         # lexical features, homoglyphs, shorteners
│   │   │   │   ├── lexical.py  homoglyph.py  shortener.py  normalizer.py
│   │   │   ├── domain_intel/         # age, registrar, DNS, TLS, ASN
│   │   │   │   ├── rdap_client.py  dns_client.py  tls_client.py  asn_lookup.py  intel_cache.py
│   │   │   ├── redirect_tracer/      # follow and record redirect chains
│   │   │   │   └── tracer.py
│   │   │   ├── content_analyzer/     # page-level signals
│   │   │   │   ├── form_inspector.py  text_signals.py  resource_ratio.py  contact_extractor.py
│   │   │   ├── brand_detector/       # impersonation logic
│   │   │   │   ├── registry.py  name_matcher.py  ownership_check.py  visual_match.py   # visual_match: perceptual hash only; 🟥 embeddings/CLIP OUT OF SCOPE
│   │   │   ├── threat_intel/         # known-bad lookups
│   │   │   │   ├── feed_loader.py  feed_lookup.py
│   │   │   └── cloaking_detector/    # compare responses across user agents
│   │   │       └── detector.py
│   │   │
│   │   ├── sandbox/                  # controlled page fetching
│   │   │   ├── browser_pool.py       # manage headless browser instances
│   │   │   ├── fetcher.py            # load URL with limits, collect DOM and network info
│   │   │   ├── screenshot.py         # full-page capture
│   │   │   └── policies.py           # timeouts, size caps, blocked resource types
│   │   │
│   │   ├── engine/                   # turns analyzer output into a verdict
│   │   │   ├── pipeline.py           # which analyzers run, in what order, with what timeouts
│   │   │   ├── feature_assembler.py  # merge analyzer outputs into one vector
│   │   │   ├── scoring/
│   │   │   │   ├── rules.py          # rule evaluation from config weights
│   │   │   │   ├── combiner.py       # ML score + rule points -> final score
│   │   │   │   ├── overrides.py      # allowlist cap, threat-feed floor
│   │   │   │   └── bands.py          # score -> label -> action
│   │   │   └── explainer/
│   │   │       ├── evidence_selector.py   # choose top findings
│   │   │       ├── llm_client.py          # explanation writer (optional)
│   │   │       └── fallback_templates.py  # template sentences when no LLM
│   │   │
│   │   ├── ml/                       # model serving only
│   │   │   ├── model_loader.py       # load versioned artifacts
│   │   │   ├── predictor.py          # fast and full model inference
│   │   │   └── shap_explainer.py     # top contributing features
│   │   │
│   │   ├── discovery/                # proactive detection
│   │   │   ├── ct_stream_listener.py # certificate-log stream consumer
│   │   │   ├── prefilter.py          # cheap lexical filter (discard ~99%)
│   │   │   ├── domain_watch.py       # new-domain handling and rescan schedule
│   │   │   ├── search_monitor.py     # brand-query search checks
│   │   │   └── maps_checker.py       # listing verification against brand registry
│   │   │
│   │   ├── clustering/
│   │   │   ├── fingerprints.py       # template hash, form signature, shared IDs
│   │   │   ├── graph_builder.py      # nodes/edges between sites, numbers, wallets
│   │   │   └── campaign_service.py   # group and name campaigns
│   │   │
│   │   ├── alerts/
│   │   │   ├── dispatcher.py         # route alert by severity and channel
│   │   │   ├── telegram.py  email.py  webhook.py   # 🟥 email.py and webhook.py OUT OF SCOPE (Telegram only)
│   │   │
│   │   ├── workers/
│   │   │   ├── celery_app.py         # Celery configuration
│   │   │   └── tasks/
│   │   │       ├── scan_tasks.py  discovery_tasks.py  cluster_tasks.py
│   │   │       ├── rescan_tasks.py  alert_tasks.py  maintenance_tasks.py
│   │   │
│   │   └── utils/
│   │       ├── url_utils.py  text_utils.py  time_utils.py  hashing.py
│   │
│   └── tests/
│       ├── unit/                     # analyzers, scoring, rules
│       ├── integration/              # API + DB + queue
│       └── fixtures/                 # sample URLs, HTML pages, expected verdicts
│
├── frontend/                         # Next.js, App Router, TypeScript
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── postcss.config.mjs
│   ├── eslint.config.mjs
│   ├── components.json               # UI-kit config
│   ├── .env.local.example
│   ├── public/                       # logo, icons, static images
│   └── src/
│       ├── proxy.ts                  # route protection by role (Next 16 renamed middleware.ts to proxy.ts; create it when auth is built, an empty file breaks the dev server)
│       ├── app/
│       │   ├── layout.tsx  globals.css  error.tsx  not-found.tsx  loading.tsx
│       │   ├── page.tsx                          # landing / quick scanner
│       │   ├── (public)/
│       │   │   ├── scan/page.tsx                 # URL scanner
│       │   │   ├── scan/[scanId]/page.tsx        # detailed analysis
│       │   │   └── report/page.tsx               # citizen report page
│       │   ├── (auth)/
│       │   │   ├── login/page.tsx
│       │   │   └── register/page.tsx
│       │   ├── (user)/
│       │   │   ├── dashboard/page.tsx            # personal security history
│       │   │   ├── devices/page.tsx              # 🟨 EXT-DEFERRED: linked extensions, pairing
│       │   │   └── settings/page.tsx             # privacy controls, allowlist
│       │   ├── (analyst)/
│       │   │   ├── console/page.tsx              # overview and triage queue
│       │   │   ├── console/cases/page.tsx        # case list
│       │   │   ├── console/cases/[caseId]/page.tsx
│       │   │   ├── console/monitoring/page.tsx   # suspicious websites monitoring
│       │   │   ├── console/map/page.tsx          # geographic fraud map
│       │   │   └── console/campaigns/[id]/page.tsx
│       │   ├── (admin)/
│       │   │   └── admin/
│       │   │       ├── page.tsx  rules/page.tsx  brands/page.tsx
│       │   │       ├── users/page.tsx  feedback/page.tsx  audit/page.tsx
│       │   └── api/                              # thin proxy routes only (e.g. auth cookie handling)
│       ├── components/
│       │   ├── ui/                   # base primitives (buttons, inputs, dialogs, tables)
│       │   ├── layout/               # navbar, sidebar, footer, language switch
│       │   ├── scanner/              # url-input, scan-progress, scan-history
│       │   ├── results/              # risk-gauge, verdict-badge, reasons-list, evidence-panel, brand-compare, shap-bars
│       │   ├── charts/               # timeline-chart, brand-bar-chart, kpi-tile
│       │   ├── feed/                 # live-feed-table, feed-filters
│       │   ├── map/                  # fraud-map, listing-popup
│       │   ├── graph/                # campaign-graph
│       │   ├── cases/                # case-header, status-stepper, notes, takedown-draft, evidence-viewer
│       │   ├── user/                 # history-timeline, device-card, privacy-controls
│       │   ├── report/               # citizen-report-form
│       │   └── admin/                # rule-editor, brand-editor, threshold-sliders, fp-queue
│       ├── lib/
│       │   ├── api-client.ts         # one place that calls the backend
│       │   ├── auth.ts               # session helpers
│       │   ├── constants.ts  utils.ts  format.ts
│       ├── hooks/                    # use-scan, use-live-feed, use-auth, use-polling
│       ├── store/                    # small client state (session, filters)
│       ├── types/                    # shared TypeScript types mirroring API schemas
│       └── i18n/
│           ├── config.ts
│           └── messages/en.json  ar.json
│
├── extension/                        # 🟨 EXT-DEFERRED (whole folder: create empty stub only, build later). Chrome / Edge MV3
│   ├── manifest.json
│   ├── package.json  tsconfig.json  vite.config.ts
│   ├── public/icons/
│   └── src/
│       ├── background/
│       │   ├── service-worker.ts         # entry: wires listeners together
│       │   ├── navigation-listener.ts    # top-level navigation events
│       │   ├── privacy-filter.ts         # skip private/local/incognito, strip query
│       │   ├── allowlist.ts              # bundled + user allowlist
│       │   ├── blocklist.ts              # downloaded confirmed-bad list
│       │   ├── verdict-cache.ts          # local TTL cache
│       │   ├── api-client.ts             # calls /check, /scan, /events
│       │   ├── scan-poller.ts            # follow up on pending verdicts
│       │   ├── decision.ts               # allow / pending / warn / block logic
│       │   └── event-queue.ts            # batch flagged events for upload
│       ├── content/
│       │   ├── form-guard.ts             # lock password/payment fields while pending
│       │   ├── banner.ts                 # checking / warning bar
│       │   └── search-badges.ts          # 🟨 EXT-DEFERRED: optional pre-click badges
│       ├── pages/
│       │   ├── blocked/                  # warning and block page
│       │   ├── popup/                    # status, pause, trust this site, report
│       │   └── options/                  # pairing, privacy settings
│       └── shared/
│           ├── types.ts  constants.ts  storage.ts  messages.ts
│
├── infra/
│   ├── docker/
│   │   ├── backend.Dockerfile
│   │   ├── worker.Dockerfile
│   │   ├── sandbox.Dockerfile        # browser image, no secrets, restricted egress
│   │   └── frontend.Dockerfile
│   └── nginx/                        # optional reverse proxy config
│
└── scripts/
    ├── seed_brands.py                # load config/brands.yaml into the DB
    ├── seed_demo_data.py             # demo detections, cases, users
    ├── fetch_feeds.py                # download threat feeds into data/raw
    ├── start_staged_sites.py         # serve own lookalike demo pages
    └── export_blocklist.py           # 🟨 EXT-DEFERRED: generate the extension blocklist file
```

## 3. Component map: one job each
| Component | Single job | Talks to |
|---|---|---|
| `api/` | Validate HTTP requests, call a service, return a schema | services |
| `services/` | Business rules and orchestration | repositories, engine, workers |
| `repositories/` | Read and write the database | db models |
| `analyzers/*` | Produce features from one kind of evidence | called by pipeline |
| `sandbox/` | Fetch pages safely and capture DOM/screenshot | called by content analyzer and workers |
| `engine/pipeline` | Decide which analyzers run and merge results | analyzers, scoring |
| `engine/scoring` | Turn features into a 0-100 score and a band | ml, config |
| `engine/explainer` | Turn findings into plain-language reasons | scoring output |
| `ml/` (backend) | Load models and predict | engine |
| `discovery/` | Find new suspicious domains, listings, results on its own | workers, pipeline |
| `clustering/` | Link sites into campaigns | repositories |
| `alerts/` | Deliver notifications | workers |
| `workers/` | Run slow or scheduled jobs | everything above |
| 🟨 `extension/background` **[DEFERRED]** | Intercept navigations and decide | backend `/check` |
| 🟨 `extension/content` **[DEFERRED]** | Protect the page while a verdict is pending | background |
| `frontend/src/app` | Pages and routing per user type | backend via `lib/api-client` |
| `frontend/src/components` | Reusable UI pieces, each with one purpose | pages |

## 4. Runtime services (docker-compose)
| Service | Role |
|---|---|
| `db` | PostgreSQL |
| `redis` | Cache and queue broker |
| `api` | FastAPI app |
| `worker` | Celery workers for scans and discovery |
| `beat` | Scheduler for re-scans and feed refresh |
| `sandbox` | Headless browser service used by workers |
| `frontend` | Next.js app |

## 5. Environment variables (names only, put values in `.env`)
Database URL, Redis URL, JWT secret and expiry, 🟨 extension token expiry (deferred), allowed CORS origins, LLM API key (optional), search API key (optional), Places API key (optional), Telegram bot token and chat ID, SMTP settings (optional), feed URLs/keys, sandbox timeout and size limits, cache TTLs (safe / suspicious), score thresholds (warn / block), model artifact version, log level, environment name.

## 6. Conventions
- **Branches:** `main` (always demoable), `dev`, one `feature/<stage>-<name>` per task. Merge small and often.
- **API:** all routes under `/api/v1`; JSON only; one error shape (code, message, details); every scan has an ID and a state (`queued`, `running`, `complete`, `failed`).
- **Verdict vocabulary (everywhere):** `allow`, `pending`, `warn`, `block`; bands `safe`, `suspicious`, `high_risk`, `likely_fraud`.
- **Analyzers return plain dictionaries** with a stable key prefix per analyzer (for example `url_*`, `domain_*`, `content_*`, `brand_*`).
- **Timeouts everywhere:** every outbound call has a time limit and a defined fallback.
- **Privacy default:** log hostnames, not full URLs with queries; never log credentials or page form contents.
- **Config over code:** thresholds, weights and brands live in `config/`.
- **Naming:** Python `snake_case`, TypeScript files `kebab-case`, React components `PascalCase`, database tables plural.
- **Commits:** small, one purpose each; run lint and tests before merging.

## 7. Tasks
1. Create the repository and the full directory tree above (empty files and `.gitkeep` where needed).
2. Add `.gitignore` (data folders, env files, build output, model artifacts if large), `.editorconfig`, `.env.example`.
3. Initialize `backend/` (dependency file, app skeleton with a health route only).
4. Initialize `frontend/` with the standard Next.js App Router (TypeScript, Tailwind) and the route-group folders.
5. 🟨 **[EXTENSION - DEFERRED]** ~~Initialize `extension/` (manifest, build config, empty entry points).~~ Only create the empty `extension/` folder with a `.gitkeep`; initialize it when the extension is picked up.
6. Write `docker-compose.yml` with `db`, `redis`, `api`, `frontend` first; add `worker`, `beat`, `sandbox` in stage 03/04.
7. Write `docs/architecture.md` (copy of sections 1-4), `docs/api-contract.md` (endpoint list, empty shapes), `docs/privacy-design.md` (principles only).
8. Fill `config/brands.yaml` with 10-20 brands for your region (English and Arabic names, official domains, keywords).
9. Add CI workflow (lint + empty test run) and the `Makefile` shortcuts.
10. Agree roles: Backend/ML, Frontend, Data-intel, Demo/Pitch (🟨 the Extension owner role is deferred), and who owns which stage.

## 8. Definition of done
- `docker compose up` starts `db`, `redis`, `api`, `frontend` with no errors.
- API health endpoint responds; frontend landing page loads and can call the health endpoint.
- 🟨 **[EXTENSION - DEFERRED]** ~~Extension builds and loads unpacked in Chrome and Edge (does nothing yet).~~ Not required now.
- Every directory in section 2 exists; `docs/` has the three starter files.
- Everyone can run the project locally from the README.

## 9. Risks and cut-lines
- Over-building the skeleton: create folders and stubs only; fill them stage by stage.
- Tooling friction (Docker, browser sandbox) eats hours: if the sandbox image is slow, defer it to stage 04.
- Cut-line: skip `infra/nginx`, `docs/decisions`, CI, and the Makefile if time is very short.

## 10. Time estimate
2-3 hours for the team, in parallel by area.
