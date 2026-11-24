# Switched off for privacy: delete later

Checking people's WhatsApp messages, SMS and email was **switched off** because reading private messages is a privacy
risk. The code is commented out or unreachable, not deleted, so we can decide the replacement first. Search the repo for
`TODO(DELETE LATER - privacy)` to find every spot.

## Backend (`backend/`)
- `app/api/v1/router.py`: `webhooks` and `whatsapp_link` routers no longer included.
- `app/api/v1/endpoints/me.py`: `/me/contacts` (add / list / delete) and `/me/alerts` commented out.
- Dormant files (delete when we decide): `api/v1/endpoints/webhooks.py`, `api/v1/endpoints/whatsapp_link.py`,
  `guard/bot_service.py`, `guard/guard_service.py`, `guard/link_extractor.py` (still reusable), `alerts/mailer.py`,
  `alerts/whatsapp.py`, `repositories/message_repo.py`, `repositories/wa_link_repo.py`, `repositories/watch_repo.py`,
  `tests/unit/test_bot_service.py`.

## Frontend (`frontend/src/`)
- Navbar and sidebar links to `/watchlist` commented out; `app/(user)/watchlist/page.tsx` now returns 404.
- Dashboard: the message alerts card and `fetchAlerts` call commented out.
- Dormant: `app/(user)/watchlist/watchlist-view.tsx`, `components/user/whatsapp-card.tsx`, the contacts / alerts / WhatsApp
  functions in `lib/api-me.ts`, and the `wa.*` / `watch.*` strings in `i18n/messages/*.json`.

## Infrastructure / settings still present (remove or keep deliberately)
- `infra/evolution/` (WhatsApp gateway containers) and its `.env`. Stop it with `yarn evolution:stop`.
- `.env` keys `EVOLUTION_API_KEY`, `EVOLUTION_API_URL`, `MANEE_WEBHOOK_BASE`, `FRAUDSHIELD_WEBHOOK_SECRET`, `MANEE_BOT_INSTANCE`.
- Linked WhatsApp sessions already on the gateway (the `Manee` bot instance and any `manee-<user>` instance): log them out.
- Tables `wa_links`, `watch_contacts`, `messages` in the database may hold test data.

## Kept on purpose (not message reading)
- Share target (`/share`, `public/manifest.webmanifest`, `public/sw.js`): the user chooses what to send.
- Browser extension, manual link scans, history, scoring.
