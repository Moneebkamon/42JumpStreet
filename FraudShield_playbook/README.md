# FraudShield Playbook

Stage-by-stage build guide for **FraudShield**, a fraud-intelligence platform that detects fraudulent links, websites and fake listings early, protects users in real time, and gives police/government analysts a triage-to-takedown workflow.

> **Status of requirements:** the only official information is the challenge title, description and objective. Registration details, format, judging criteria and deadlines have not been announced. Everything here is a **recommendation [REC]**. When the organizers publish requirements, they override this playbook.
>
> **No code in this playbook.** Each stage defines the goal, the directories and components (with the single job of each), the tasks, the interfaces and the definition of done.

## Scope markers (read this first)
Current decision: **the browser extension is NOT executed for now.** It is deferred, not deleted, so nothing is forgotten.

| Marker | Meaning | Action now |
|---|---|---|
| 🟨 **[EXTENSION - DEFERRED]** | Anything that exists only to support the browser extension (extension code, `/check`, device pairing, extension events, blocklist export, extension tests/demo step). | **Do not build yet. Do not delete.** Keep the stub/note and revisit when the core is done. |
| 🟥 **[OUT OF SCOPE]** | Other items cut from this build (embeddings/CLIP, 2FA, Google sign-in, partner keys and webhooks, email/webhook alerts). | Do not build. |
| (no marker) | In scope. | Build. |

Every stage file repeats these markers next to the affected rows, tasks and checks. Search the folder for `🟨` to list everything deferred for the extension, and `🟥` for everything out of scope.

## How to use it
1. Do stages in order. Each stage lists what it depends on and what "done" means.
2. A component has **one job**. If you find yourself adding a second job to a file, create a new component instead.
3. Tick the checklist at the end of each stage before moving on.
4. Time estimates are rough and assume a team of 3-4. The hackathon length is unknown, so use the cut-lines in each stage.

## Stages
| # | File | Purpose | Est. |
|---|---|---|---|
| 00 | `00_initialization_and_architecture.md` | Repo, full directory layout, component map, conventions, local environment | 2-3h |
| 01 | `01_data_and_feature_extraction.md` | Datasets, labels, feature extractors (URL, domain, content) | 4h |
| 02 | `02_model_and_scoring_engine.md` | Fast/full models, rules, risk score, calibration | 4h |
| 03 | `03_backend_core_api_and_pipeline.md` | Scan/check API, job queue, caching, pipeline orchestration | 4-5h |
| 04 | `04_website_analysis_sandbox.md` | Sandboxed browser fetch, content, brand and visual analysis | 4h |
| 05 | `05_frontend_foundation_and_scanner.md` | Next.js app shell, scanner page, result and detail pages | 4h |
| 06 | `06_accounts_auth_and_device_pairing.md` | Users, roles, auth (in scope); 🟨 extension pairing, device events and user history (deferred) | 3h (about 2h without the 🟨 parts) |
| 07 | `07_browser_extension.md` | 🟨 **[EXTENSION - DEFERRED]** Chrome/Edge MV3 protection: warn, block, Form Guard | ~~5h~~ 0h now |
| 08 | `08_proactive_discovery.md` | Certificate-log feed, pre-filter, auto-scoring, cache pre-warming | 4h |
| 09 | `09_analyst_console_cases_evidence.md` | Triage queue, cases, evidence, takedown reports, public report page | 5h |
| 10 | `10_maps_and_search_monitoring.md` | Maps listing verifier, search-result monitor, geographic map | 3-4h |
| 11 | `11_clustering_explanations_alerts.md` | Campaign clustering, AI explanations, alerts | 3-4h |
| 12 | `12_admin_hardening_and_localization.md` | Admin, security hardening, Arabic/RTL, privacy controls | 3h |
| 13 | `13_testing_demo_and_pitch.md` | Test data, evaluation, demo script, pitch, freeze | 3h |

## Dependency map
```
00 -> 01 -> 02 -> 03 -> 04 -> 05
                    \-> 06 -> 07
              03 -> 08 -> 11
              03 + 04 + 06 -> 09
              03 + 04 -> 10
        all -> 12 -> 13
```

## Priority if time runs short (assuming police/government is the main audience)
Must keep: 00-05, 08, 09. Then: 06 (auth and roles only), 10 (one scenario).
🟨 **[EXTENSION - DEFERRED]:** 07 entirely (Lite mode, Form Guard, search badges), plus the pieces of 03, 06, 08, 12 and 13 that only serve it.
🟥 **[OUT OF SCOPE]:** visual (CLIP) embeddings, 2FA, Google sign-in, partner keys and webhooks, email/webhook alert channels.

## Naming and ethics rules used throughout
- Project name: **FraudShield** (working name; check availability before branding).
- Analyze suspected phishing only inside the sandbox; never enter real credentials; respect each API's terms and rate limits; do not scrape Maps.
- Demo only with your own staged lookalike pages, clearly labeled as simulated.
- The system recommends; a human analyst confirms before anything is published or sent outside.
