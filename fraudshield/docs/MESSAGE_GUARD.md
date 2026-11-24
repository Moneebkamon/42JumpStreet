# Message guard (SMS + WhatsApp) and alert email

A signed-in user adds phone numbers on the **Watch list** page. When a message with a link reaches one of those numbers,
FraudShield scans each link (offline analyzers only: the sender is untrusted, so the server never opens their links).

| Worst link band | Action | What happens |
|---|---|---|
| `high_risk`, `likely_fraud` | **blocked** | stored, alert email sent (if the user's alerts are on), WhatsApp warning sent back (if Evolution is configured) |
| `suspicious` | monitor | stored, shown in the user's alerts and history, no email |
| `safe` | allowed | stored so it appears in the history |

Messages without links are ignored and not stored. Several accounts may watch the same number; each gets its own record.

## Environment (names only; copy from `.env.example`)
- `FRAUDSHIELD_WEBHOOK_SECRET` (required): both webhooks refuse every request without it.
- Email: `FRAUDSHIELD_SMTP_HOST/PORT/USER/PASSWORD/SSL`, `FRAUDSHIELD_MAIL_FROM`. With no SMTP host, each email is written as an
  `.html` file in `data/interim/outbox/` (override with `FRAUDSHIELD_OUTBOX`), so it can be opened in a browser. Nothing is sent.
- WhatsApp reply (optional): `EVOLUTION_API_URL`, `EVOLUTION_INSTANCE`, `EVOLUTION_API_KEY`.

## WhatsApp via Evolution API
Use Manee's own Evolution instance: `infra/evolution/` (its own containers, database, volumes and port 8081; copy `.env.example` to `.env`, fill in fresh secrets, `docker compose up -d`). Do not reuse another team's or company's Evolution instance or keys. Set the instance webhook to:

    POST http://<fraudshield-backend>:8000/api/v1/webhooks/whatsapp      header  X-Webhook-Secret: <secret>
    events: MESSAGES_UPSERT

The watched number is the number the instance is connected to (the `sender` field of the payload), so add that number
(as **WhatsApp** or **Phone**) to the watch list. Messages you sent yourself (`fromMe`) and group chats are ignored.
The compose file maps `host.docker.internal` to the host, so the container can reach the backend on port 8000. Set `EVOLUTION_API_URL=http://localhost:8081`.

## SMS (Twilio-style)
Point the provider's incoming-message webhook at:

    POST http://<fraudshield-backend>:8000/api/v1/webhooks/sms?secret=<secret>

Form fields used: `From`, `To`, `Body`. `To` is the watched number. (Twilio cannot add custom headers, so the secret is in the URL.)

## Browser extension
The website's **Extension** page creates a one-time linking code. Paste it in the extension popup under "FraudShield account".
The extension then checks `GET /api/v1/ext/config` every 5 minutes (and at start-up): when the account switch is **off**, it shows
no badges. Links seen on pages are uploaded to `POST /api/v1/ext/visits` and appear in the user's history. Remove the device on
the website and the extension unlinks itself on its next check.

## Not done yet
- Phone/email ownership verification (OTP): contacts are stored with `verified=false`.
- Live delivery has not been tested against a real Evolution instance, SMS provider or SMTP server (no credentials in the repo).

## Linking WhatsApp from the website (no manual Evolution setup per user)
The operator starts the gateway once with `yarn evolution` (needs `infra/evolution/.env`). Members then open **Watch list**, enter their
number, scan the QR code and are connected: the backend creates one gateway instance per account (`manee-<hash>`), sets its webhook
automatically and maps incoming messages to the account by instance name. Backend env: `EVOLUTION_API_URL` (default `http://localhost:8081`),
`EVOLUTION_API_KEY` (same value as in `infra/evolution/.env`; never sent to the browser), `FRAUDSHIELD_WEBHOOK_SECRET`,
optional `MANEE_WEBHOOK_BASE` (default `http://host.docker.internal:8000`) and `MANEE_MAX_WA_LINKS` (default 20 linked accounts).
Endpoints: `POST /me/whatsapp/connect`, `GET /me/whatsapp/status`, `POST /me/whatsapp/refresh`, `DELETE /me/whatsapp`.
Risks to tell users: the connection is unofficial (the number can be banned by WhatsApp) and linking gives Manee access to the chats of that account; only links are stored.
The Evolution v2 endpoint shapes were written from its documentation and are NOT yet verified against a running gateway.
