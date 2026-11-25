<div align="center">

# Manee | منيع

**An early-warning system for scam and phishing links, built around UAE brands.**

*Team 42 Jump Street · 42 Common Core Hackathon*

![Backend](https://img.shields.io/badge/backend-FastAPI%20%7C%20Python%203.11%2B-009688)
![Frontend](https://img.shields.io/badge/frontend-Next.js%20%7C%20TypeScript-000000)
![Extension](https://img.shields.io/badge/extension-Chrome%20MV3-4285F4)
![Languages](https://img.shields.io/badge/languages-English%20%7C%20Arabic-informational)

</div>

> The product was renamed from **FraudShield** to **Manee** (Arabic: منيع, "impregnable"). Some folder names (`fraudshield/`,
> `FraudShield_playbook/`), the `FRAUDSHIELD_*` environment variables and a few documents still use the old name.

---

## Table of contents

1. [Introduction](#1-introduction)
2. [Key features](#2-key-features)
3. [How it works](#3-how-it-works)
4. [Repository structure](#4-repository-structure)
5. [Prerequisites](#5-prerequisites)
6. [Quick start](#6-quick-start)
7. [Optional components](#7-optional-components)
8. [Running with Docker](#8-running-with-docker)
9. [Configuration reference](#9-configuration-reference)
10. [Testing](#10-testing)
11. [Demo walkthrough](#11-demo-walkthrough)
12. [Documentation index](#12-documentation-index)
13. [Troubleshooting](#13-troubleshooting)
14. [Known limitations](#14-known-limitations)
15. [Roadmap](#15-roadmap)
16. [Contributing](#16-contributing)
17. [Security and privacy](#17-security-and-privacy)

---

## 1. Introduction

Scam links reach people through search results, maps listings, WhatsApp and SMS, and by the time a link is reported it has
usually already cost someone money. Manee tries to flag them **earlier** and **where people actually meet them**.

Paste a link and Manee returns a risk score with plain-language reasons. It scores a link from its text and domain **without
opening it**. An optional staff-only "safe browser" deep scan loads the page inside an isolated headless browser. Results are
automated early warnings, **not final verdicts**.

Manee has three audiences:

| Audience | What they get |
|---|---|
| **Members (the public)** | A free account, a link scanner, a private history, a watch list of emails and phone numbers, a message guard for WhatsApp/SMS (test mode, to become *Share to Manee*), and a Chrome extension that labels Google Search and Maps results |
| **Analysts** | A triage queue of newly detected suspicious domains, cases with an enforced status flow, frozen SHA-256 evidence, and takedown report drafts |
| **Admins** | Everything above plus an editable scoring configuration, a false-positive queue with allowlist, and the audit log |

## 2. Key features

| Feature | Description |
|---|---|
| **Link scanner** | 16+ rules (look-alike characters, brand impersonation, URL shorteners, pressure words, domain age), OpenPhish feed lookup, and a small ready-made URL model used as a weak extra signal |
| **Deep scan (staff)** | Headless Chromium in a hardened sandbox: public addresses only, no downloads, no form submission. Checks forms, hidden frames, obfuscated scripts, phone numbers, wallets, redirect chains |
| **Browser extension** | Chrome extension that labels Google Search and Maps results, blocks high-risk pages with a warning screen, guards risky downloads, flags fake "customer service" numbers and fake UAE PASS sign-ins. Can be linked to a member account |
| **Message guard** *(test mode; will become **Share to Manee**)* | Links in WhatsApp (and SMS) messages sent to a watched number are scored through our own Evolution API gateway. Dangerous ones are marked blocked and an alert email is sent. Only links are stored, never chat text |
| **Early detection** | Scores newly issued certificate domains against UAE brand names. Runs on a simulated sample unless a live Certificate Transparency stream is enabled |
| **Analyst console** | Triage queue, cases, enforced status flow, frozen evidence with integrity verification, audit log |
| **Takedown drafts** | Text only. Nothing is ever sent automatically |
| **Citizen reports** | Public form with spam protection; reports raise priority but never block anything on their own |
| **Roles** | `user`, `analyst`, `admin` |
| **Localization** | English and Arabic (right-to-left) for navigation and member pages |

## 3. How it works

```
                      ┌──────────────────────────────────────────────┐
  Chrome extension ──►│                                              │
  (labels, blocking,  │            FastAPI backend  :8000            │──► SQLite (data/)
   download guard)    │                                              │
                      │  analyzers → scoring engine → explanations   │──► OpenPhish / threat feeds
  Next.js website ───►│  accounts · guard · discovery · cases        │
  :3000 (proxy /api)  │                                              │──► Safe browser (Playwright,
                      └───────▲───────────────────────▲──────────────┘     deep scan, staff only)
                              │                       │
                 Evolution API gateway          Certificate Transparency
                 (WhatsApp, optional)           stream (optional, simulated by default)
```

1. **Analyzers** extract signals from a link: normalization, lexical features, homoglyphs/punycode, shorteners, brand matching
   (17 UAE brands, including leet digits and one-letter typos), and domain lookups (RDAP age, DNS, TLS).
2. The **scoring engine** combines rule weights (`fraudshield/config/rule_weights.yaml`) into a 0-100 score and a risk band, and
   produces human-readable reasons.
3. The **extension** runs its own local scoring first (instant, offline-capable) and asks the backend about gray-zone links.
4. **Discovery** feeds newly seen domains into the same engine and fills the analyst triage queue.

## 4. Repository structure

```
42JumpStreet/
├── README.md                     ← you are here
├── extension/                    ← upstream browser-extension snapshot (FraudShield v2.4, as received)
├── fraudshield/                  ← the Manee application
│   ├── backend/                  ← FastAPI service
│   │   ├── app/
│   │   │   ├── alerts/           ←   email / WhatsApp / Telegram alert senders
│   │   │   ├── analyzers/        ←   URL, domain and content analyzers
│   │   │   ├── api/v1/endpoints/ ←   REST endpoints (scan, auth, me, devices, cases, ...)
│   │   │   ├── clustering/       ←   campaign grouping
│   │   │   ├── core/             ←   config, auth, security helpers
│   │   │   ├── discovery/        ←   proactive detection (CT stream, maps, search)
│   │   │   ├── engine/           ←   scoring engine and explanations
│   │   │   ├── guard/            ←   WhatsApp/SMS message guard
│   │   │   ├── ml/               ←   optional URL model wrapper
│   │   │   ├── repositories/     ←   database access
│   │   │   ├── sandbox/          ←   safe-browser deep scan
│   │   │   ├── schemas/          ←   request/response models
│   │   │   ├── services/         ←   business logic
│   │   │   └── main.py           ←   application entry point
│   │   ├── alembic/              ←   migrations
│   │   ├── tests/                ←   unit and integration tests
│   │   └── requirements.txt
│   ├── frontend/                 ← Next.js website (public, user, analyst, admin areas)
│   ├── extension/                ← Manee browser extension (v2.4, linked to accounts)
│   ├── config/                   ← brands, rule weights, risk bands, TLD risk, allowlist
│   ├── data/                     ← raw / interim / processed data and samples
│   ├── docs/                     ← architecture, scoring spec, privacy, demo script, ...
│   ├── infra/                    ← Dockerfiles, WhatsApp gateway, certstream config
│   ├── ml/                       ← ready phishing-URL model and its evaluation
│   ├── scripts/                  ← create users, seed data, fetch feeds, run evaluations
│   ├── docker-compose.yml        ← all-in-Docker mode
│   ├── package.json              ← convenience scripts (yarn backend, yarn frontend, ...)
│   ├── .env.example              ← environment variable names
│   └── CURRENT_STAGE.md          ← handoff file: current status and known gaps
├── FraudShield_playbook/         ← stage-by-stage build plan (00-13)
├── Manee_image_prompts.md        ← pitch-deck image prompts
├── Manee-numbered-slide-images/  ← pitch-deck slide images
└── presentation.pptx             ← pitch deck
```

> **Two extension folders.** `fraudshield/extension/` is the one to load in Chrome: it contains the upstream detection engine
> **plus** the Manee account link. The root `extension/` is the unmodified upstream snapshot (its own README, changelog and
> `eval/` accuracy scale) kept for reference and for future merges.

## 5. Prerequisites

| Tool | Version | Needed for | Check |
|---|---|---|---|
| Git | any recent | cloning | `git --version` |
| Python | 3.11+ | backend | `python --version` |
| Node.js | 20+ | website, extension tests | `node --version` |
| Yarn | 1.x | website | `yarn --version` |
| Docker Desktop | recent, **running** | WhatsApp gateway and all-in-Docker mode only | `docker --version` |
| Google Chrome | recent | the extension | |

The commands below use Windows paths (`backend\.venv\Scripts\...`) because the `yarn` scripts do. On macOS/Linux, replace
`Scripts` with `bin` and run the equivalent commands from `fraudshield/package.json` by hand.

## 6. Quick start

Everything runs from the `fraudshield/` folder.

```bash
git clone https://github.com/Moneebkamon/42JumpStreet.git
cd 42JumpStreet/fraudshield
```

### 6.1 Install

```bash
yarn setup:backend              # creates backend/.venv and installs backend dependencies
yarn --cwd frontend install     # installs website dependencies
```

Only if you want the staff **deep scan**:

```bash
backend\.venv\Scripts\python -m playwright install chromium
```

### 6.2 (Optional) create staff accounts

Members register on the website themselves. Staff accounts are created from the command line:

```bash
python scripts/create_user.py admin1 admin --generate      # random password -> data/interim/credentials-admin1.txt
python scripts/create_user.py analyst1 analyst --generate
```

### 6.3 (Optional) seed demo data

```bash
yarn seed
```

### 6.4 Run

Open two terminals, both inside `fraudshield/`:

```bash
yarn backend       # API       -> http://localhost:8000   (interactive docs: /docs)
yarn frontend      # website   -> http://localhost:3000
```

Open <http://localhost:3000>, press **Create account**, and you are signed in as a member. Paste a link on the home page to scan it.

## 7. Optional components

### 7.1 Chrome extension

1. Open `chrome://extensions` and turn on **Developer mode**.
2. Press **Load unpacked** and choose **`fraudshield/extension/`**.
3. *(Optional, to link it to your account)* On the website open **Devices** and press **Connect my browser extension**. The code
   is handed to the extension automatically; if it is not found on the page, copy the code into the extension popup instead.
4. The website's **Active / Inactive** switch now controls the extension and Google pages you browse are added to your history.

Unlinked, the extension works fully on its own (local scoring only). Run its tests with:

```bash
cd fraudshield/extension
node test.js                     # scoring tests (178 cases)
npm run eval                     # accuracy scale on public phishing/legit lists
```

Details: `fraudshield/extension/README.md` and `fraudshield/extension/CHANGELOG.md`.

### 7.2 WhatsApp message guard with Evolution API (demo / test mode)

> **This feature will be replaced by "Share to Manee".** The WhatsApp linking below is a **demo / test mode** that shows the
> message-guard idea end to end. In the real version Manee will **not** link to anyone's WhatsApp or read their chats. The user
> picks the one message they doubt and shares it to Manee (phone Share menu → Manee, already working at `/share` on installed
> phones), or forwards it to Manee's official WhatsApp Business number. Manee then checks **only the links in what was sent**.
> Until then, use a spare number and only chats with people who know about the test.

**What it is.** [Evolution API](https://github.com/EvolutionAPI/evolution-api) is an open-source WhatsApp gateway. Manee runs its
**own** copy (`fraudshield/infra/evolution/`: its own containers, Postgres, Redis and port 8081) and uses it to connect a WhatsApp
number as a *linked device*. Incoming messages are sent to the Manee backend webhook; Manee extracts the links, scores them,
stores only the link and the verdict (never the message text), and shows them under **Message alerts**.

```
WhatsApp phone ◄─QR─► Evolution API :8081 ──webhook──► Manee backend :8000 ──► Message alerts (website) + alert email
```

**Requirements:** Docker Desktop **running**, the backend and website already working (section 6), and a spare WhatsApp number.
Never reuse anyone else's gateway or keys.

**How to run it**

1. Generate three random secrets and keep each one (never commit them):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(24))"
   ```
2. Gateway settings. Copy `fraudshield/infra/evolution/.env.example` to `fraudshield/infra/evolution/.env` and fill in
   `EVOLUTION_API_KEY` (secret 1) and `POSTGRES_PASSWORD` (secret 2).
3. Start the gateway from `fraudshield/` (the first run downloads images):
   ```bash
   yarn evolution                  # stop later with: yarn evolution:stop
   ```
   Check it is up: open <http://localhost:8081/manager> and log in with `EVOLUTION_API_KEY`.
4. Start the backend with the secrets in its environment (PowerShell). `EVOLUTION_API_KEY` must equal the value from step 2:
   ```powershell
   $env:FRAUDSHIELD_WEBHOOK_SECRET = "<secret 3>"
   $env:EVOLUTION_API_KEY = "<same key as infra/evolution/.env>"
   yarn backend
   ```
   Then start the website in another terminal with `yarn frontend`.
5. On the website: sign in, open **Watch list → Connect WhatsApp**, enter the number, and scan the QR code with that phone
   (WhatsApp → Linked devices → Link a device). Wait for **Connected**.
6. Test: from another phone send `http://adcb-secure-login.top/verify` (a made-up look-alike; do not open it). It shows under
   **Message alerts** as *Blocked*, and an alert email is written to `fraudshield/data/interim/outbox/` (or sent, if SMTP is set).
7. When finished: **Disconnect** on the Watch list page, then `yarn evolution:stop`.

**Optional backend variables:** `EVOLUTION_API_URL` (default `http://localhost:8081`), `MANEE_WEBHOOK_BASE` (default
`http://host.docker.internal:8000`, how the gateway reaches the backend), `MANEE_MAX_WA_LINKS` (default 20).

**If it does not work:** the QR never appears or never connects → Docker Desktop is not running, or `EVOLUTION_API_KEY` differs
between `infra/evolution/.env` and the backend terminal. No alert appears → check `FRAUDSHIELD_WEBHOOK_SECRET` is set in the
backend terminal and the sender is not yourself or a group (both are ignored).

> **Risks.** The link to WhatsApp is unofficial, so WhatsApp can ban the number. Linking gives Manee technical access to that
> account's chats, which is why this is test mode only. The gateway listens on your own machine only. The gateway calls were
> written from Evolution's documentation and have not been verified against a long-running gateway. More:
> `fraudshield/docs/MESSAGE_GUARD.md`.

SMS works through a Twilio-style webhook (`/api/v1/webhooks/sms?secret=...`) and needs a provider number. Optional and untested live.

**Share to Manee (the production path, no linking):** on a phone, open the Manee site in Chrome, install it (Add to Home screen),
then in WhatsApp long-press a message → Share → **Manee**. The link check runs on the shared text only. It needs HTTPS or localhost.

### 7.3 Alert emails

Set these in the same terminal before `yarn backend`, with **your own** mailbox or provider:

```powershell
$env:FRAUDSHIELD_SMTP_HOST = "smtp.example.com"
$env:FRAUDSHIELD_SMTP_PORT = "587"
$env:FRAUDSHIELD_SMTP_USER = "<user>"
$env:FRAUDSHIELD_SMTP_PASSWORD = "<password>"
$env:FRAUDSHIELD_MAIL_FROM = "Manee <alerts@your-domain>"
```

With no SMTP host set nothing is sent: each alert is saved as an `.html` file in `fraudshield/data/interim/outbox/` so you can open it in a browser.

### 7.4 Threat feeds and early detection

```bash
python scripts/fetch_feeds.py        # download OpenPhish (and other) feeds into the local store
python scripts/generate_ct_sample.py # build the simulated certificate sample
python scripts/run_discovery.py      # score it and fill the analyst triage queue
```

A **live** Certificate Transparency stream is available in Docker (`docker compose --profile live up -d certstream ct-listener`).
It reads public logs only (about 3 GB/hour while running) and never contacts the domains it sees.

### 7.5 Ready URL model

`fraudshield/ml/` documents the optional `urlbert-tiny-v2-phishing-classifier` model (MIT, 3.7 M parameters) used as a weak extra
signal. Without the model files the app runs exactly the same (`ml_available: 0`). See `fraudshield/ml/README.md`.

## 8. Running with Docker

```bash
cd fraudshield
docker compose build        # large first download (Chromium base image)
docker compose up -d        # website on http://localhost:3000, API on 127.0.0.1:8000
docker compose down         # stop
```

Containers run without extra privileges, with a read-only filesystem and resource limits (see `fraudshield/docs/sandbox.md`).

> This mode has **not** been re-verified since member accounts and the WhatsApp guard were added. The local run in section 6 is the
> tested path.

## 9. Configuration reference

Copy `fraudshield/.env.example` to `fraudshield/.env` for the general settings. Secrets are never committed.

| Variable | Purpose | Default |
|---|---|---|
| `FRAUDSHIELD_WEBHOOK_SECRET` | Shared secret on WhatsApp/SMS webhooks (**required** for the guard) | none |
| `FRAUDSHIELD_SMTP_HOST` / `_PORT` / `_USER` / `_PASSWORD` / `_SSL` | Alert email delivery | empty → write to outbox |
| `FRAUDSHIELD_MAIL_FROM` | Sender address for alerts | none |
| `FRAUDSHIELD_OUTBOX` | Where unsent emails are saved | `data/interim/outbox/` |
| `EVOLUTION_API_URL` | WhatsApp gateway address | `http://localhost:8081` |
| `EVOLUTION_API_KEY` | Gateway key (must match `infra/evolution/.env`) | none |
| `EVOLUTION_INSTANCE` | Gateway instance name | none |
| `MANEE_WEBHOOK_BASE` | URL the gateway uses to reach the backend | `http://host.docker.internal:8000` |
| `MANEE_MAX_WA_LINKS` | Max WhatsApp links stored per member | `20` |
| `FRAUDSHIELD_NETWORK` | `0` disables live lookups (RDAP/DNS/TLS) | `1` |
| `FRAUDSHIELD_ML` | `0` disables the URL model | `1` |
| `SCORE_THRESHOLD_WARN` / `_BLOCK` | Score cut-offs | `60` / `80` |

Scoring behaviour (rule weights, brands, TLD risk, risk bands) lives in `fraudshield/config/*.yaml` and can be edited by admins in
the website's scoring editor, with preview and history.

## 10. Testing

```bash
cd fraudshield
yarn test                          # backend tests (offline: no network, no real messages)

cd extension
node test.js                       # extension scoring tests
node test-rdap.js                  # extension RDAP cache test
```

Accuracy evaluations are in `fraudshield/scripts/` (`run_golden.py`, `run_real_eval.py`) and in `fraudshield/extension/eval/`.
Do not quote offline numbers as real-world accuracy (see [limitations](#14-known-limitations)).

## 11. Demo walkthrough

About three minutes (full script: `fraudshield/docs/demo-script.md`):

1. **Scan:** on the home page paste `https://adcb-secure-login.example.com/verify` and read the score and reasons.
2. **Account:** create an account, check a few links, open **History**.
3. **Extension:** link it, switch it off on the website, watch the labels disappear.
4. **Message guard (test mode, to be replaced by Share to Manee):** connect WhatsApp, send yourself the test link from another phone, see it blocked plus the alert email.
5. **Analyst:** sign in as an analyst, open a case from a scan, freeze evidence, create a takedown draft.
6. **Admin:** sign in as admin and open the audit log.

## 12. Documentation index

| Document | What is in it |
|---|---|
| `fraudshield/README.md` | Application-level README |
| `fraudshield/CURRENT_STAGE.md` | Live status per build stage and known gaps (**read first when resuming work**) |
| `fraudshield/docs/architecture.md` | System design |
| `fraudshield/docs/scoring-spec.md` | How scores are computed |
| `fraudshield/docs/api-contract.md` | REST API contract |
| `fraudshield/docs/privacy-design.md` | What is stored and why |
| `fraudshield/docs/evidence-handling.md` | Evidence freezing and verification |
| `fraudshield/docs/MESSAGE_GUARD.md` | WhatsApp / SMS guard |
| `fraudshield/docs/MESSAGE_GUARD_REMOVAL_PLAN.md` | Status of the guard (test mode) and the checklist to replace it with Share to Manee |
| `fraudshield/docs/discovery.md` | Early-detection pipeline |
| `fraudshield/docs/sandbox.md` | Safe-browser and container hardening |
| `fraudshield/docs/demo-script.md`, `pitch.md` | Demo and pitch material |
| `fraudshield/extension/README.md`, `CHANGELOG.md` | Extension usage and version history |
| `FraudShield_playbook/` | Original stage-by-stage build plan |

## 13. Troubleshooting

| Problem | Fix |
|---|---|
| `yarn backend` fails with "python not found" / venv missing | Run `yarn setup:backend` first; make sure Python 3.11+ is on `PATH` |
| Website loads but scans fail | The backend is not running on port 8000. Start `yarn backend` |
| Port 3000 or 8000 already in use | Stop the other process, or change the port in the `yarn` script |
| Deep scan says the browser is missing | Run `backend\.venv\Scripts\python -m playwright install chromium` |
| Extension shows no labels | Reload it on `chrome://extensions`, then reload the Google page |
| "Connect my browser extension" shows a code to paste | The extension was not detected on the page. Reload the extension and the website tab, or paste the code in the popup |
| WhatsApp QR never connects | Docker Desktop must be running; check `EVOLUTION_API_KEY` matches in both places |
| No alert emails arrive | No SMTP host is set. Look in `data/interim/outbox/` |
| `docker compose up` fails | Use the local run (section 6); the Docker mode is not re-verified |
| Line-ending warnings from Git on Windows | Harmless (`core.autocrlf`); do not mass-convert files |

## 14. Known limitations

- Early detection uses a **simulated** certificate sample by default. Real-data accuracy is not measured; do not quote offline numbers as product accuracy.
- The WhatsApp message guard is a **test mode** (linked device through Evolution API) and will be replaced by Share to Manee. Live WhatsApp, SMS and SMTP delivery, and the extension account link, have not been tested against real services end to end.
- The extension's URL-only detection is strong on UAE brand impersonation but weak on links with nothing suspicious in the text
  (see `fraudshield/extension/CHANGELOG.md`, entry 2.4). `.ae` domains have no public RDAP record, so the domain-age check never fires for them.
- Evidence freezing stores the analysis, not screenshots or page HTML.
- Sessions are signed cookies without server-side revoke; there is no password reset.
- Only a limited set of brands is covered by the rules; the URL model is biased by top-level domain.
- Results are early warnings, not legal or final verdicts.

## 15. Roadmap

- Sign-in with UAE PASS (and TAMM where available). Needs a registered service provider and credentials.
- One-time-code verification of phone numbers and emails (currently stored as unverified).
- **Replace the WhatsApp linking with "Share to Manee"** and the official WhatsApp Business forward-to-number route: users send only the message they doubt and Manee never links to or reads their chats. The Evolution API mode stays a test/demo tool until then; the removal steps are in `fraudshield/docs/MESSAGE_GUARD_REMOVAL_PLAN.md`.
- List lookup and page scan to catch links that look clean in text.
- Screenshots and HTML in frozen evidence; clustering and a campaign graph.
- Arabic for the older staff pages; brand editor and user management for admins.

## 16. Contributing

1. Create a branch from `main` (`git checkout -b feature/<short-name>`).
2. Keep changes focused; one component has one job.
3. Run `yarn test` (backend) and `node test.js` (extension) before pushing.
4. For extension changes, add an entry to `fraudshield/extension/CHANGELOG.md` and bump the version in `manifest.json` and `package.json`.
5. Update `fraudshield/CURRENT_STAGE.md` when a build step ends.
6. Open a pull request into `main`.

## 17. Security and privacy

- Never commit secrets: `.env`, `infra/evolution/.env`, credentials files, API keys. Only variable **names** belong in `.env.example`.
- The WhatsApp guard is test-mode only: it can technically see a linked account's chats, so it is to be replaced by Share to Manee, where the user sends only the message they choose. Only links and verdicts are stored, never message text. Removal checklist: `fraudshield/docs/MESSAGE_GUARD_REMOVAL_PLAN.md`.
- The deep scan runs only for staff, inside an isolated browser: public addresses only, no downloads, no form submission.
- Takedown drafts are text only; nothing is sent to anyone automatically.
- The extension sends data to Manee only when an account is linked (visited Google result links, reports). Unlinked, it works locally.
- See `fraudshield/docs/privacy-design.md` for what is stored and why.

---

<div align="center">

Built at the 42 Common Core Hackathon by Team **42 Jump Street**.

</div>
