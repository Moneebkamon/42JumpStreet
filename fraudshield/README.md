# FraudShield

An early-warning tool for scam and phishing links, built around UAE brands. Paste a link and get a risk score with plain-language
reasons. Analysts get an early-detection feed, a triage queue, cases with frozen evidence, and takedown report drafts.

It scores a link from its text and domain without opening it. An optional "safe browser" deep scan loads the page in an isolated
headless browser. Results are automated early warnings, not final verdicts.

## What is in it

| Part | What it does |
|---|---|
| Link scanner | 16+ rules (look-alike characters, brand impersonation, shorteners, pressure words, domain age), OpenPhish feed lookup, and a small ready-made URL model (weak extra signal) |
| Early detection | Scores newly issued certificate domains against UAE brand names before anyone reports them. Runs on a **simulated** sample unless you wire a live stream |
| Analyst console | Triage queue, cases with an enforced status flow (reason required), SHA-256 frozen evidence with verify, audit log |
| Takedown drafts | Text only. Wording stays "suspected" until a case is confirmed. Nothing is ever sent |
| Citizen reports | Public form with spam protection; reports raise priority but never block anything |
| Login | Analyst and admin roles. Public: scanning and reporting |

## Run it (Windows, from `fraudshield/`)

```
yarn setup:backend                 # one time: Python venv + dependencies
yarn --cwd frontend install        # one time
python scripts/create_user.py admin1 admin --generate     # writes a random password to data/interim/credentials-admin1.txt
python scripts/create_user.py analyst1 analyst --generate

yarn backend                       # API on http://localhost:8000  (docs at /docs)
yarn frontend                      # app on http://localhost:3000
yarn test                          # backend tests (offline)
```

Set `FRAUDSHIELD_AUTH=0` to turn login off for a quick local demo (everyone is then treated as an admin).
Optional data: `python scripts/fetch_feeds.py --download openphish`, `python scripts/generate_ct_sample.py`, `python scripts/run_discovery.py`.

## Docker

```
docker compose build     # large first download (Chromium base image)
docker compose up -d     # http://localhost:3000 (API on 127.0.0.1:8000)
# create staff accounts inside the container (passwords are printed by this command, so keep the output private):
docker compose exec backend python -c "import secrets;from app.core.auth import hash_password as h;from app.repositories import user_repo as u;pw=secrets.token_urlsafe(12);u.upsert('admin1',h(pw),'admin');print(pw)"
# fill the early-detection feed with the SIMULATED certificate sample (in Git Bash prefix with MSYS_NO_PATHCONV=1):
docker compose exec backend python scripts/run_discovery.py --sample /srv/samples/ct_stream.jsonl --reset
docker compose down      # stop it
```

Containers run without extra privileges, read-only, with limits. See `docs/sandbox.md`.

## Demo path (about 3 minutes)

1. Home: paste `https://adcb-secure-login.example.com/verify`. Read the score and reasons.
2. Open the saved result, mark it as a scam.
3. Sign in as an analyst. Open a case from that scan, move it to "under review" with a reason.
4. Freeze evidence, verify a hash, create a takedown draft (note "NOT YET CONFIRMED"), confirm the case, draft again.
5. Open `/report` in a private window and send a report. See it appear in the triage queue.
6. Sign in as admin and open the audit log to show who did what.

More: `docs/discovery.md` (early detection), `docs/ready-model-eval.md` (the URL model), `docs/sandbox.md` (safe browser and containers), `docs/demo-script.md`, `docs/pitch.md`, `docs/performance.md`, `docs/golden-report.md`.
Current status and known gaps: `CURRENT_STAGE.md`. (`docs/architecture.md`, `scoring-spec.md`, `evidence-handling.md`, `privacy-design.md` are still empty placeholders.)

## Honest limits

- Early detection uses a simulated certificate sample here. Real-data accuracy is not measured; do not quote the offline numbers
  as product accuracy.
- Evidence freezing stores the analysis, not screenshots or page HTML yet.
- Sessions are signed cookies without server-side revoke; there is no password reset or user-management page yet.
- Only a few brands are covered by the rules; the URL model is biased by top-level domain.
