# Stage 05: Frontend Foundation and Scanner

## Goal
Set up the Next.js app shell and deliver the first user-visible flow: paste a URL, watch progress, see a score with reasons, and open a detailed analysis page.

## Depends on
Stages 00 and 03 (04 improves the results shown).

## Components and their single jobs
| Component | Job | Location |
|---|---|---|
| Root layout | Global shell, fonts, language direction (LTR/RTL) | `src/app/layout.tsx` |
| Landing / quick scanner | Entry page with the URL input | `src/app/page.tsx` |
| Scanner page | Submit URL and show live progress | `src/app/(public)/scan/page.tsx` |
| Analysis page | Full result for one scan | `src/app/(public)/scan/[scanId]/page.tsx` |
| API client | Only place that calls the backend; typed responses | `src/lib/api-client.ts` |
| Types | Mirror backend schemas | `src/types/` |
| Polling hook | Poll scan state until complete or timeout | `src/hooks/use-polling.ts`, `use-scan.ts` |
| URL input | Validate and submit a URL | `components/scanner/url-input.tsx` |
| Scan progress | Step indicator for analysis stages | `components/scanner/scan-progress.tsx` |
| Scan history | Recent scans list | `components/scanner/scan-history.tsx` |
| Risk gauge | Display 0-100 score | `components/results/risk-gauge.tsx` |
| Verdict badge | Colored band label | `components/results/verdict-badge.tsx` |
| Reasons list | Top reasons in plain language | `components/results/reasons-list.tsx` |
| Evidence panel | Screenshot, domain facts, form targets | `components/results/evidence-panel.tsx` |
| Brand compare | Side-by-side with the real brand site | `components/results/brand-compare.tsx` |
| SHAP bars | Contribution of top features | `components/results/shap-bars.tsx` |
| Layout components | Navbar, sidebar, footer, language switch | `components/layout/` |
| UI primitives | Buttons, inputs, tables, dialogs | `components/ui/` |

## Design rules
- One purpose per component; pages only assemble components.
- All backend calls go through `api-client`; no direct fetches in components.
- Risk colors: red / orange / amber / green with text labels (never color alone).
- Every result shows **reasons**, **confidence** and a **"report false positive"** action.
- Build with RTL in mind from the start (logical spacing, no left/right hard-coding), even if Arabic strings come in stage 12.

## Tasks
1. Initialize shell: layout, navbar, theme, error/loading/not-found pages.
2. Implement `api-client`, types and the polling hook.
3. Build the scanner page: input -> submit -> progress -> result.
4. Build the result components (gauge, badge, reasons, evidence panel).
5. Build the analysis page with tabs: Overview, Domain/Infra, Content, Brand match, Model explanation, Raw data.
6. Add scan history (local list first; account-based later).
7. Add empty, loading and error states for every data view.
8. Connect to the running API in docker-compose and test with fixture URLs.

## Interfaces
- Consumes: `POST /scan`, `GET /scan/{id}`.
- Shows: score, band, confidence, reasons, evidence references, SHAP features.

## Done when
- A user can scan a URL end to end and read a clear explanation.
- The analysis page shows screenshot, domain facts and the matched brand where available.
- Loading, failure and timeout states look intentional.

## Risks and cut-lines
- Over-styling: use the component kit and finish function first.
- Cut-line: skip SHAP bars, scan history and brand-compare until the end; keep gauge, badge, reasons.

## Time estimate
About 4 hours (can run in parallel with stage 04).
