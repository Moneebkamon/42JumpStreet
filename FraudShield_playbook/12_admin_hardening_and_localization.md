# Stage 12: Admin, Hardening and Localization

## Goal
Make the platform controllable and trustworthy: an admin area for rules and brands, security hardening, privacy controls and Arabic/English support.

## Depends on
Stages 06, 08, 09.

## Components and their single jobs
| Component | Job | Location |
|---|---|---|
| Admin endpoint | Thresholds, rule weights, users, model version | `api/v1/endpoints/admin.py` |
| Brand endpoint | Create/update brand registry entries | `api/v1/endpoints/brands.py` |
| Allowlist endpoint | Manage allowlist and promoted false positives | `api/v1/endpoints/allowlist.py` |
| 🟥 Partners endpoint **[OUT OF SCOPE]** | Issue and revoke partner API keys with scopes | `api/v1/endpoints/partners.py`, `db/models/partner_key.py` (not built) |
| Feedback service | Review false-positive reports, promote to allowlist, queue for retraining | `services/feedback_service.py` |
| Admin pages | Rules, brands, users, feedback queue, audit view | `src/app/(admin)/admin/...` |
| Admin components | Rule editor, brand editor, threshold sliders, FP queue | `components/admin/` |
| i18n | English/Arabic messages and direction switch | `src/i18n/config.ts`, `messages/en.json`, `ar.json` |
| 🟨 Extension strings **[EXT - DEFERRED]** | Localized block page and popup | `extension/src/pages/` |
| Hardening checklist | Items listed below | `docs/privacy-design.md`, `docs/architecture.md` |

## Hardening checklist
- Secrets only in environment variables; none committed; `.env.example` names only.
- CORS restricted to known origins. 🟨 (Deferred: extension calls authenticated by device token.)
- Rate limits on scan, check, auth and the public report endpoints; request-size limits.
- Role guard on every analyst/admin endpoint (checked server-side).
- Sandbox isolation verified: no secrets, no internal network, non-root, resource limits.
- Output encoding of any fetched content shown in the UI (treat as hostile); screenshots and HTML snapshots served from a separate path, never executed.
- Audit log for admin and analyst actions; no deletion of audit entries from the UI.
- Logs: hostnames only; no form contents or credentials.
- Dependencies pinned; run a vulnerability scan on both lockfiles.
- Data retention: scheduled cleanup of old events per user setting; user delete-history works.
- Backups of the database for the demo environment.

## Localization rules
- Full RTL layout verified on the console, block page and popup.
- Brand registry stores Arabic and English names; matcher handles both.
- Test on Arabic scam page samples (text signals and OCR-free checks first).
- Numbers, dates and the risk labels are localized; the score stays 0-100.

## Tasks
1. Implement admin and brand/allowlist endpoints with role guards. 🟥 (Out of scope: partner endpoints.)
2. Build the admin pages and components.
3. Implement the false-positive review flow (queue -> decision -> allowlist/retrain list).
4. Add i18n to the frontend; verify RTL. 🟨 **[EXTENSION - DEFERRED]** ~~and the extension pages~~.
5. Go through the hardening checklist and fix gaps; write results into `docs/privacy-design.md`.
6. Add a simple retention cleanup task.
7. Run a basic dependency vulnerability scan.

## Done when
- An admin can change a threshold or a rule weight and see the effect without redeploying.
- A false positive reported from the web scanner reaches the queue and can be promoted to the allowlist. 🟨 (Reporting from the extension is deferred.)
- Arabic and English both work in the console and the scanner result page. 🟨 (The extension block page is deferred.)
- The hardening checklist has no open critical items.

## Risks and cut-lines
- Time sink in translations: translate the demo path first (scanner, block page, console queue).
- 🟥 **[OUT OF SCOPE]:** partner keys. Cut-line for the rest: skip audit view page and retention task; keep thresholds, brands, FP queue, RTL on the demo path.

## Time estimate
About 3 hours.
