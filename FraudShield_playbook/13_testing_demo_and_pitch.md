# Stage 13: Testing, Demo and Pitch

## Goal
Prove the system works with measured numbers, prepare a reliable demo that doesn't depend on live feeds, and finalize the pitch. Freeze features first.

## Depends on
All previous stages (minimum: 00-05, 08, 09).

## Components and deliverables
| Item | Purpose | Location |
|---|---|---|
| Golden test set | ~30 URLs (phishing, benign, hard negatives) with expected bands | `backend/tests/fixtures/` |
| Evaluation report | Precision, recall, false-positive rate on hard negatives (time split) | `ml/reports/` |
| Latency report | Cache-hit, fast-path and deep-scan timings measured on your machine | `docs/` (new file `performance.md`) |
| Staged sites | Your own lookalike pages, investment page, campaign set | `data/samples/`, `scripts/start_staged_sites.py` |
| Demo seed | Users, detections, cases, listings, a campaign | `scripts/seed_demo_data.py` |
| Recorded sample stream | Offline version of the certificate feed | `data/samples/` |
| Demo script | Minute-by-minute run sheet | `docs/demo-script.md` (new) |
| Backup recording | Screen recording of the full demo | outside repo |
| Pitch deck/notes | Pitch text and slide outline | `docs/pitch.md` (new) |
| README | Run instructions for judges | `README.md` |

## Testing checklist
1. Unit tests: analyzers, scoring rules, bands, case status transitions, role guards.
2. Integration tests: scan flow with cache, evidence hashing. 🟨 **[EXTENSION - DEFERRED]** check flow and device pairing tests.
3. Golden set run with a written pass criterion.
4. 🟨 **[EXTENSION - DEFERRED]** Extension manual tests in Chrome and Edge: staged phishing page, benign page, slow backend, offline backend.
5. Privacy check: confirm that logs contain no query strings. 🟨 (Deferred: what the extension sends (hosts only) and that incognito is skipped.)
6. Failure drills: kill the worker, kill Redis, disable the LLM, disconnect the network; confirm graceful behavior.
7. Fresh-clone test: a teammate runs the project from the README on a clean machine.

## Demo scenario (about 5 minutes)
1. **Story (30s):** a victim searches "ExampleBank support" and sees a fake listing.
2. **Scan (60s):** paste a staged phishing URL; score, reasons, side-by-side with the real brand page.
3. 🟨 **[EXTENSION - DEFERRED] Extension (60s):** click the staged lookalike link; warning/block appears before typing; "continue anyway" and "report false positive" work; the event appears in the user dashboard. **Skip this step in the current demo and use the 60s elsewhere** (for example, a longer scan walkthrough with the side-by-side brand comparison).
4. **Proactive feed (60s):** a newly issued staged domain appears with a score and a Telegram alert; "nobody reported this."
5. **Analyst view (60s):** triage queue -> open case -> frozen evidence with hashes -> campaign graph -> takedown draft (draft only).
6. **Maps (45s):** a fake branch listing flagged because its phone/website mismatch and link to the scam site.
7. **Safe case (15s):** a legitimate bank loads silently, low score.

Use only staged pages labeled as simulated.

## Pitch structure (about 3 minutes)
1. Problem: scams live and die faster than blocklists; victims start from search and Maps.
2. Insight: detect on day one from certificate logs, then protect the click, then give police evidence.
3. Demo highlights (the three most visual moments).
4. Why it's different: proactive discovery, campaign graph, explainable verdicts, analyst workflow with hashed evidence. 🟨 (Deferred: privacy-preserving browser protection. Mention it as the next step, not as a feature.)
5. Honest limits and next steps: dataset size, regional brands, partner integrations, formal evidence process, hosting requirements.
6. Close: what a bank or a police unit can plug in tomorrow. 🟨 (Deferred: "a browser", until the extension exists.)

Adjust to the organizers' judging criteria once published; none are assumed here.

## Freeze rules
- **Feature freeze** 3-4 hours before the deadline; only fixes after that.
- Seed all demo data and test the offline path; never depend on a live feed or API on stage.
- Record a backup video after the final build.
- Keep one working branch tagged for the demo; no merges after the tag except critical fixes.

## Done when
- The demo runs from a fresh clone with seeded data and the offline stream.
- The numbers you quote (precision, false positives, latencies) come from your reports.
- Backup video exists; pitch rehearsed at least twice with timing.

## Time estimate
About 3 hours, plus rehearsal time.
