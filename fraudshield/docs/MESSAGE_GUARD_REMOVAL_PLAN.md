# Message guard: status and removal plan

## Status (2026-11-25)

The WhatsApp / SMS **message guard** is a **demo / test mode**. It is switched on in the code so the idea can be shown end to end:
a member links a WhatsApp number through our own Evolution API gateway, and links in incoming messages are scored. Only the
link and the verdict are stored, never the message text.

Linking an account gives Manee technical access to that account's chats, and the link is unofficial (the number can be banned).
So this is **not** the production design.

**Production plan: Share to Manee.** The user picks the one message they doubt and shares it to Manee (phone Share menu →
Manee, already working at `/share`), or forwards it to Manee's official WhatsApp Business number. Manee checks only the links
in what was sent and never links to or reads anyone's chats. When that is in place, remove the guard using the checklist below.

## What the demo mode consists of

| Area | Files |
|---|---|
| Routers | `backend/app/api/v1/router.py` includes `webhooks` and `whatsapp_link` |
| Endpoints | `api/v1/endpoints/webhooks.py`, `api/v1/endpoints/whatsapp_link.py`, and in `me.py`: `/me/contacts` (add / list / delete) and `/me/alerts` |
| Guard logic | `guard/bot_service.py`, `guard/guard_service.py`, `guard/link_extractor.py` (reusable: keep it for Share to Manee) |
| Alerts | `alerts/mailer.py`, `alerts/whatsapp.py` |
| Storage | `repositories/message_repo.py`, `wa_link_repo.py`, `watch_repo.py`; tables `wa_links`, `watch_contacts`, `messages` |
| Tests | `tests/unit/test_bot_service.py`, the message-guard tests in `tests/unit/test_accounts_guard.py` |
| Frontend | `app/(user)/watchlist/` (page and `watchlist-view.tsx`), `components/user/whatsapp-card.tsx`, the `/watchlist` links in `components/layout/navbar.tsx` and `components/user/user-sidebar.tsx`, the message-alerts card and `fetchAlerts` in `app/(user)/dashboard/page.tsx`, the contacts / alerts / WhatsApp functions in `lib/api-me.ts`, the `wa.*` and `watch.*` strings in `i18n/messages/*.json` |
| Infrastructure | `infra/evolution/` (gateway containers) and its `.env`; `yarn evolution` scripts in `package.json` |
| Settings | `EVOLUTION_API_KEY`, `EVOLUTION_API_URL`, `EVOLUTION_INSTANCE`, `MANEE_WEBHOOK_BASE`, `MANEE_MAX_WA_LINKS`, `MANEE_BOT_INSTANCE`, `FRAUDSHIELD_WEBHOOK_SECRET` |

## Removal checklist

Do these when Share to Manee replaces the guard.

1. **Stop the gateway:** `yarn evolution:stop`. In `http://localhost:8081/manager` log out and delete the `Manee` bot instance and every `manee-<user>` instance.
2. **Backend routes:** remove the `webhooks` and `whatsapp_link` imports and `include_router` lines from `router.py`; remove `/me/contacts` and `/me/alerts` from `me.py` (and the `contacts` count in `/me/summary`).
3. **Delete the backend files** listed above (except `guard/link_extractor.py`, which Share to Manee can reuse) and their tests.
4. **Database:** drop the tables `wa_links`, `watch_contacts`, `messages`, or delete the old database file, since they may hold test data.
5. **Frontend:** delete the `watchlist` folder and `whatsapp-card.tsx`; remove the nav and sidebar links, the dashboard alerts card, the unused functions in `lib/api-me.ts`, and the `wa.*` / `watch.*` strings.
6. **Infrastructure and settings:** delete `infra/evolution/` and its `.env`, remove the `evolution` scripts from `package.json`, and remove the keys listed under "Settings" from `.env` and `.env.example`.
7. **Docs:** remove the WhatsApp section from the root `README.md` (section 7.2) and update `docs/MESSAGE_GUARD.md` and `CURRENT_STAGE.md`.
8. **Check:** run `yarn test`, `npx tsc --noEmit` in `frontend/`, and confirm `/share` still works.

## Kept on purpose

- Share target: `/share`, `public/manifest.webmanifest`, `public/sw.js`. The user chooses what to send.
- Browser extension, manual link scans, history and scoring.
