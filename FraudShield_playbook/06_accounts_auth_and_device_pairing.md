# Stage 06: Accounts, Auth and Device Pairing

## Goal
Add users with roles, secure login, extension pairing tokens, and the data needed for the personal security dashboard. Google sign-in is optional and never required.

> **Scope in this stage**
> - In scope: users, roles, secure login, route protection, role guards, feedback (false-positive reports from the web scanner).
> - 🟨 **[EXTENSION - DEFERRED]:** device model, pairing codes and tokens, extension event upload, personal history built from extension events, the Devices page. Keep them as stubs; do not build now.
> - 🟥 **[OUT OF SCOPE]:** Google sign-in, 2FA, `partner` role.

## Depends on
Stages 03 and 05.

## Components and their single jobs
| Component | Job | Location |
|---|---|---|
| User model and repo | Store users, roles, password hash, status | `db/models/user.py`, `repositories/user_repo.py` |
| 🟨 Device model and repo **[EXT - DEFERRED]** | Store paired extension devices and token metadata | `db/models/device.py`, `repositories/device_repo.py` |
| 🟨 Event model and repo **[EXT - DEFERRED]** | Store flagged events per user/device | `db/models/event.py`, `repositories/event_repo.py` |
| Security helpers | Password hashing, token creation and verification | `core/security.py` |
| Auth service | Register, login, refresh, role checks | `services/auth_service.py` |
| 🟨 Device service **[EXT - DEFERRED]** | Create short-lived pairing codes; exchange for a device token; revoke | `services/device_service.py` |
| 🟨 History service **[EXT - DEFERRED]** | Return the user's flagged history and summary counts (fed by extension events) | `services/history_service.py` |
| Dependencies | Current user, role guard (🟨 current device: deferred) | `api/deps.py` |
| Endpoints | `auth`, `feedback`; 🟨 `devices`, `events` (deferred) | `api/v1/endpoints/` |
| Route protection | Redirect by role | `frontend/src/proxy.ts` (Next 16 name for middleware) |
| Auth pages | Login, register | `src/app/(auth)/login`, `register` |
| User dashboard pages | Settings; 🟨 history and devices (deferred, depend on the extension) | `src/app/(user)/dashboard`, `devices`, `settings` |
| User components | Privacy controls; 🟨 history timeline, device card (deferred) | `components/user/` |

## Roles
`citizen` (default), `analyst`, `supervisor`, `admin`, 🟥 ~~`partner` (API only)~~ **[OUT OF SCOPE]**. Role checks happen in the API dependency layer, not only in the UI.

## Decisions
- **A normal platform account is sufficient.** 🟨 (Deferred: the extension also works without an account (local protection only); an account adds sync, history and dashboard.)
- 🟥 **[OUT OF SCOPE] Google sign-in:** ~~use only `openid email profile`. Do not request Gmail scopes; email scanning is roadmap only.~~
- 🟨 **[EXTENSION - DEFERRED] Extension pairing:** user clicks "link extension" in the web app -> gets a short-lived code -> enters it in the extension -> backend returns a device token stored in the extension. Tokens are revocable per device.
- 🟨 **[EXTENSION - DEFERRED] Privacy of extension events:** event sync is opt-in; stores flagged events only (host, score, verdict, reasons, time, user action); retention period configurable; user can delete history.

## Tasks
1. Create the user table with a migration. 🟨 (Deferred: device and event tables.)
2. Implement security helpers and auth service; register/login/refresh endpoints.
3. Implement dependencies (current user, role guard). 🟨 (Deferred: device auth.)
4. 🟨 **[EXTENSION - DEFERRED]** Implement device pairing and revocation endpoints.
5. 🟨 **[EXTENSION - DEFERRED]** Implement event upload (batch) and history endpoints; add data deletion and export.
6. Build login/register pages, route protection and the settings page. 🟨 (Deferred: history and devices pages.)
7. Add the privacy controls component (retention, delete data). 🟨 (Deferred: extension sync on/off.)
8. Seed demo users for each role.
9. Tests: role guard denies correctly. 🟨 (Deferred: pairing code expires; revoked device is rejected.)

## Interfaces (names only)
- `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`
- 🟨 `POST /devices/pair-code`, `POST /devices/exchange`, `DELETE /devices/{id}` **[EXTENSION - DEFERRED]**
- 🟨 `POST /events` (batch), `GET /events` (user history), `DELETE /events` **[EXTENSION - DEFERRED]**
- `POST /feedback` (false-positive report)

## Done when
- A user can register and log in. 🟨 (Deferred: link a device and see a populated history.)
- Each role sees only what it is allowed to see; tests prove it.
- 🟨 **[EXTENSION - DEFERRED]** A user can delete their history and unlink a device.

## Risks and cut-lines
- Auth bugs are costly: use well-tested libraries; do not invent crypto.
- 🟥 **[OUT OF SCOPE]:** Google sign-in, 2FA. Cut-line for the rest: skip refresh tokens and data export until the end.

## Time estimate
About 3 hours.
