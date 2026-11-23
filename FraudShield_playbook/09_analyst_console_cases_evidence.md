# Stage 09: Analyst Console, Cases and Evidence (Police / Government Layer)

## Goal
Give analysts a workflow: triage detections, open cases, preserve hashed evidence, track status, and prepare takedown reports for human review. Add a public report page for citizens.

## Depends on
Stages 03, 04, 06 (roles), 08 (detections).

## Components and their single jobs
| Component | Job | Location |
|---|---|---|
| Case models/repos | Cases, linked sites, actions | `db/models/case.py`, `action.py`, `repositories/case_repo.py`, `action_repo.py` |
| Evidence model/repo | Evidence items with type, path, SHA-256, capture time | `db/models/evidence.py`, `repositories/evidence_repo.py` |
| Audit model/repo | Who did what and when | `db/models/audit_log.py`, `repositories/audit_repo.py` |
| Citizen report model/repo | Public submissions | `db/models/citizen_report.py`, `repositories/citizen_report_repo.py` |
| Case service | Case lifecycle and allowed status transitions | `services/case_service.py` |
| Evidence service | Freeze, hash, store and verify evidence | `services/evidence_service.py` |
| Priority service | Triage priority = risk x exposure (reports, users hit, brand importance, recency) | `services/priority_service.py` |
| Takedown service | Build report drafts for registrar/hosting, search/browser safety teams, impersonated brand, telecom; export only | `services/takedown_service.py` |
| Citizen report service | Accept reports, run the engine, raise priority | `services/citizen_report_service.py` |
| Audit service | Write audit entries for every sensitive action | `services/audit_service.py` |
| Endpoints | `cases`, `evidence`, `takedowns`, `citizen_reports`, `stats` | `api/v1/endpoints/` |
| Console overview | Triage queue + KPIs | `src/app/(analyst)/console/page.tsx` |
| Case list/detail | Cases and a single case | `console/cases/page.tsx`, `console/cases/[caseId]/page.tsx` |
| Monitoring page | Suspicious websites table | `console/monitoring/page.tsx` |
| Case components | Header, status stepper, notes, takedown draft, evidence viewer | `components/cases/` |
| Public report page | Citizen submits link/screenshot/number | `src/app/(public)/report/page.tsx`, `components/report/citizen-report-form.tsx` |

## Case statuses
`New -> Under review -> Confirmed -> Takedown requested -> Taken down / Closed` and `False positive` from any review state. Transitions are enforced in the case service; each change records user, reason and time.

## Evidence package (what is frozen)
Full-page screenshot, HTML snapshot, redirect chain, form targets, RDAP/DNS snapshot, TLS certificate, hosting/ASN, capture time in UTC, tool version. Each item is hashed (SHA-256); every view or export is written to the audit log. Whether this satisfies legal evidence standards is for the organizers' legal staff to decide; the system provides a tamper-evident record.

## Human-in-the-loop rules
- The AI recommends; an analyst confirms before a site goes on a published blocklist or a report is sent.
- The takedown generator **drafts and exports only**; it never sends.
- Wording says "suspected" until an analyst confirms; no statements about individuals.
- Citizen reports are signals that raise priority; they never block by themselves.
- Rate-limit and add an anti-abuse step on the public report form.

## Tasks
1. Create case, evidence, action, audit and citizen-report tables with migrations.
2. Implement repositories, then the services (audit first so everything else can use it).
3. Implement the priority service and wire it into the queue endpoint.
4. Implement evidence freezing from an existing deep scan; verify hash on read.
5. Implement the takedown draft builder with templates per recipient type.
6. Implement endpoints with role guards (analyst/supervisor only).
7. Build the console overview, case list/detail, monitoring table and case components.
8. Build the public report form and backend flow with abuse protection.
9. Seed demo cases (one confirmed, one false positive, one with a campaign).
10. Tests: invalid status transition rejected; evidence hash mismatch detected; non-analyst denied.

## Interfaces (names only)
- `GET /cases`, `POST /cases`, `GET/PATCH /cases/{id}`, `POST /cases/{id}/notes`
- `POST /cases/{id}/evidence`, `GET /evidence/{id}`, `GET /evidence/{id}/verify`
- `POST /cases/{id}/takedown-drafts`, `GET /takedowns/{id}/export`
- `POST /citizen-reports`, `GET /stats`

## Done when
- From the feed, an analyst can open a case, freeze evidence, see hashes, change status with a reason, and export a takedown draft.
- Audit log shows each action.
- A citizen report appears in the queue with a risk result and reference number.

## Risks and cut-lines
- Scope creep: build the single happy path first (detection -> case -> evidence -> draft).
- 🟥 **[OUT OF SCOPE]:** two-factor login, partner webhooks. Cut-line for the rest: skip SLA timers and supervisor stats; keep queue, case, evidence, draft, audit.
- 🟨 **[EXTENSION - DEFERRED]:** a user's extension history does not feed the triage priority yet (the "users hit" exposure input uses scans and citizen reports only).

## Time estimate
About 5 hours.
