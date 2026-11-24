# Manee | منيع

An early-warning tool for scam and phishing links, built around UAE brands. Paste a link and get a risk score with plain-language
reasons. Members get a personal account with a browser extension, a link history, and a message guard that checks links arriving by
WhatsApp or SMS. Analysts get an early-detection feed, a triage queue, cases with frozen evidence, and takedown report drafts.

It scores a link from its text and domain without opening it. An optional "safe browser" deep scan (staff only) loads the page in an
isolated headless browser. Results are automated early warnings, not final verdicts.

> The product was renamed from FraudShield to **Manee** (Arabic: منيع). The folder name, `FRAUDSHIELD_*` environment variables and some docs still use the old name.

## What is in it

| Part | What it does |
|---|---|
| Link scanner | 16+ rules (look-alike characters, brand impersonation, shorteners, pressure words, domain age), OpenPhish feed lookup, and a small ready-made URL model (weak extra signal) |
| Member accounts | Anyone can register. A member has a dashboard, a private history of links they checked or visited, a watch list of emails and phone numbers, and linked browsers |
| Browser extension | Chrome extension that labels Google Search and Maps results. Linked to an account, it can be switched on or off from the website and uploads visited links to the member's history |
| Message guard | Links in WhatsApp (and SMS) messages sent to a watched number are scored. Dangerous ones are marked blocked and an alert email is sent |
| Roles | `user` (member), `analyst`, `admin`. Deep search and the staff console are staff only |
| Early detection | Scores newly issued certificate domains against UAE brand names. Runs on a **simulated** sample unless you wire a live stream |
| Analyst console | Triage queue, cases with an enforced status flow, SHA-256 frozen evidence with verify, audit log |
| Takedown drafts | Text only. Nothing is ever sent |
| Citizen reports | Public form with spam protection; reports raise priority but never block anything |
| Languages | English and Arabic (right-to-left) for the navigation and member pages; older staff pages are still English |

## 1. What to install first (Windows)

| Tool | Why | Check |
|---|---|---|
| Git | clone the project | `git --version` |
| Python 3.11 or newer | backend | `python --version` |
| Node.js 20 or newer and Yarn 1.x | website | `node --version`, `yarn --version` |
| Docker Desktop | only for the WhatsApp gateway (and the optional all-in-Docker mode) | `docker --version`, and Docker Desktop must be **running** |
| Google Chrome | the browser extension | |

## 2. First-time setup (run from the `fraudshield/` folder)

```
yarn setup:backend                 # Python virtual environment + backend dependencies
yarn --cwd frontend install        # website dependencies
backend\.venv\Scripts\python -m playwright install chromium    # only if you want staff deep search
```

Optional: a staff account (members register on the website, they do not need this):

```
python scripts/create_user.py admin1 admin --generate       # random password is written to data/interim/credentials-admin1.txt
python scripts/create_user.py analyst1 analyst --generate
```

## 3. Run it

Open separate terminals, all inside `fraudshield/`.

**Website and backend (always):**

```
yarn backend      # API on http://localhost:8000  (API docs at /docs)
yarn frontend     # website on http://localhost:3000
```

Open http://localhost:3000, press **Create account**, and you are signed in as a member.
`yarn test` runs the backend tests (offline, no network, no real messages).

## 4. Optional: WhatsApp message guard

Manee runs its **own** WhatsApp gateway (Evolution API, public open-source image) from `infra/evolution/`. Do not point it at anyone
else's gateway or reuse anyone else's keys. The gateway needs Docker Desktop to be running.

1. Make three random secrets (run it three times, keep each output, never commit them):
   ```
   python -c "import secrets; print(secrets.token_urlsafe(24))"
   ```
2. Gateway settings: copy `infra/evolution/.env.example` to `infra/evolution/.env` and fill in `EVOLUTION_API_KEY` and `POSTGRES_PASSWORD`.
3. Start the gateway (first run downloads images):
   ```
   yarn evolution          # stop it later with: yarn evolution:stop
   ```
4. Start the backend with the secrets in its environment (PowerShell). `EVOLUTION_API_KEY` must equal the value in step 2:
   ```
   $env:FRAUDSHIELD_WEBHOOK_SECRET = "<third secret>"
   $env:EVOLUTION_API_KEY = "<same key as infra/evolution/.env>"
   yarn backend
   ```
5. In the website: **Watch list**, **Connect WhatsApp**, type your number, scan the QR code with that phone
   (WhatsApp, Linked devices, Link a device). Wait for "Connected".
6. Test: from another phone, send a message containing `http://adcb-secure-login.top/verify` (a made-up look-alike; do not open it).
   It appears under **Message alerts** as Blocked.

Things to know: the link to WhatsApp is unofficial, so WhatsApp can ban the number (use a spare number for testing). Linking gives
Manee access to that account's chats; only links are stored, never the chat text. The gateway only listens on your own machine.
More detail: `docs/MESSAGE_GUARD.md`. Optional extra backend variables: `EVOLUTION_API_URL` (default `http://localhost:8081`),
`MANEE_WEBHOOK_BASE` (default `http://host.docker.internal:8000`), `MANEE_MAX_WA_LINKS` (default 20).

SMS works through a Twilio-style webhook (`/api/v1/webhooks/sms?secret=...`) and needs a provider number; it is optional and untested live.

## 5. Optional: alert emails

Set these in the same terminal before `yarn backend` (use your **own** mailbox or provider; never reuse someone else's credentials):

```
$env:FRAUDSHIELD_SMTP_HOST = "smtp.example.com"
$env:FRAUDSHIELD_SMTP_PORT = "587"
$env:FRAUDSHIELD_SMTP_USER = "<user>"
$env:FRAUDSHIELD_SMTP_PASSWORD = "<password>"
$env:FRAUDSHIELD_MAIL_FROM = "Manee <alerts@your-domain>"
```

With no SMTP host set, nothing is sent: each alert email is saved as an `.html` file in `data/interim/outbox/` so you can open it in a browser.

## 6. Optional: the Chrome extension

1. Chrome: open `chrome://extensions`, turn on **Developer mode**, press **Load unpacked**, choose the `extension/` folder.
2. On the website open **Extension**, press **Create a linking code**, copy it.
3. Click the extension icon, paste the code under the account box and press link.
4. The **Active / Inactive** switch on the website now controls the extension (it checks every 5 minutes and when Chrome starts).
   Pages you browse on Google are added to your history. Unlinked, the extension still works on its own.

Details: `extension/README.md`. It is not yet tested in real Chrome against the full stack.

## 7. Docker (everything in containers)

```
docker compose build     # large first download (Chromium base image)
docker compose up -d     # http://localhost:3000 (API on 127.0.0.1:8000)
docker compose down      # stop it
```

This runs the website and backend. It has not been re-checked since member accounts and the WhatsApp guard were added, so the steps
above are the tested way to run the project. Containers run without extra privileges, read-only, with limits (`docs/sandbox.md`).

## 8. Planned, not built

- Sign-in with UAE PASS (and TAMM if an integration is available). Needs a registered service provider and credentials from the UAE PASS team.
- One-time-code verification of phone numbers and emails (today they are stored as unverified).
- The official WhatsApp Business route (users forward a message to Manee's number) as the real-user path instead of linking a personal account.

## Demo path (about 3 minutes)

1. Home: paste `https://adcb-secure-login.example.com/verify`. Read the score and reasons.
2. Create an account, check a few links, open **History**.
3. Link the extension, switch it off on the website, and watch the labels stop.
4. Connect WhatsApp, send yourself the test link from another phone, see it blocked and the alert email.
5. Sign in as an analyst, open a case from a scan, freeze evidence, create a takedown draft.
6. Sign in as admin and open the audit log.

More: `docs/discovery.md`, `docs/ready-model-eval.md`, `docs/sandbox.md`, `docs/MESSAGE_GUARD.md`, `docs/demo-script.md`, `docs/pitch.md`.
Current status and known gaps: `CURRENT_STAGE.md`.

## Honest limits

- Early detection uses a simulated certificate sample here. Real-data accuracy is not measured; do not quote the offline numbers as product accuracy.
- Live WhatsApp, SMS and SMTP delivery and the extension account link have not been tested against real services yet.
- Evidence freezing stores the analysis, not screenshots or page HTML yet.
- Sessions are signed cookies without server-side revoke; there is no password reset yet.
- Only a few brands are covered by the rules; the URL model is biased by top-level domain.
