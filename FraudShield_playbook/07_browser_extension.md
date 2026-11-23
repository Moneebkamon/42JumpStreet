# Stage 07: Browser Extension (Chrome / Edge, Manifest V3)

> 🟨 **[EXTENSION - DEFERRED] This entire stage is NOT executed for now. Do not ignore it: it is postponed, not cancelled.**
> Revisit after stages 00-05, 08 and 09 are done. Until then: do not build anything below, and do not delete the `extension/` stub folder from Stage 00. Everything in this file is kept as the future plan.
> Backend pieces that only exist for the extension are also marked 🟨 in stages 03, 06, 08, 12 and 13.

## Goal
Protect users in real time: check each top-level navigation, warn or block dangerous sites with an explanation, protect password fields while a verdict is pending, and report flagged events to the user dashboard.

## Depends on
Stages 03 (check endpoint) and 06 (pairing). Stage 08 improves the blocklist.

## 🟨 Components and their single jobs (deferred)
| Component | Job | Location |
|---|---|---|
| Service worker entry | Wire all background modules together | `src/background/service-worker.ts` |
| Navigation listener | React to top-level navigations before load and on commit | `src/background/navigation-listener.ts` |
| Privacy filter | Skip private/local/internal URLs and incognito; strip queries; reduce to host | `src/background/privacy-filter.ts` |
| Allowlist | Bundled top-site list + user's trusted sites | `src/background/allowlist.ts` |
| Blocklist | Downloaded list of confirmed-bad hosts; instant local match | `src/background/blocklist.ts` |
| Verdict cache | Local TTL cache of past verdicts | `src/background/verdict-cache.ts` |
| API client | Calls `/check`, `/scan/{id}`, `/events`, `/blocklist` with the device token and timeouts | `src/background/api-client.ts` |
| Scan poller | Follow up on pending verdicts for a short time | `src/background/scan-poller.ts` |
| Decision module | Map verdict + score to allow / pending / warn / block | `src/background/decision.ts` |
| Event queue | Batch flagged events for upload | `src/background/event-queue.ts` |
| Form Guard | Lock password/payment fields and submission while verdict is pending | `src/content/form-guard.ts` |
| Banner | "Checking..." and warning bar | `src/content/banner.ts` |
| Search badges | Optional pre-click badges on search results | `src/content/search-badges.ts` |
| Block/warn page | Explain why, show real brand domain, offer actions | `src/pages/blocked/` |
| Popup | Status, pause, trust this site, report false positive | `src/pages/popup/` |
| Options | Pairing code entry, privacy settings | `src/pages/options/` |

## 🟨 Delivery tiers (deferred)
- **Lite mode (build first):** navigation listener, privacy filter, allowlist, cache, API client, decision, block/warn page, popup, event queue. Permissions: navigation events, storage, alarms, host access to your API only.
- **Guard mode (advanced):** adds content scripts (Form Guard, banner, search badges). Requires broad host access; state the reason clearly to users and reviewers.
- **Instant blocking (advanced):** local blocklist matched in the listener; optionally declarative network rules.

## 🟨 Behavior rules (deferred)
1. **Before a request leaves:** privacy filter -> allowlist -> blocklist -> local cache. Most visits end here with no network call.
2. **Unknown host:** call `/check` with a short timeout. Return `block` -> redirect the tab to the block page; `warn` -> warning page with "continue anyway"; `pending` -> let the page load, start Form Guard, poll the scan.
3. **Late verdict:** if a pending scan returns danger, show a warning even though the page loaded.
4. **Failure policy:** backend unreachable -> fail open for unknown sites; keep local blocklist protection active.
5. **Redirects:** re-check on commit because the final URL may differ.
6. **User control:** pause protection, trust this site, report false positive, delete history.
7. **Privacy:** hostname-only lookups by default (path only for shared-hosting hosts or locally suspicious URLs); no page content upload; incognito off by default; sync of flagged events is opt-in.
8. **Block page:** state what was flagged, why (reasons), the official domain when it is an impersonation, and a deliberate extra step to continue.

## 🟨 Tasks (ALL DEFERRED - do not execute now)
1. Create the manifest with minimal permissions (Lite mode) and the build pipeline; load unpacked in Chrome and Edge.
2. Implement privacy filter, allowlist, cache, API client and decision module.
3. Implement the navigation listener and the redirect to the block/warn page.
4. Build the block/warn page, popup and options (pairing).
5. Implement event queue and upload; confirm events appear in the user dashboard (stage 06).
6. Add blocklist download on a schedule and local matching.
7. Add Form Guard and banner (Guard mode).
8. Optional: search badges using batched host lookups.
9. Test with your staged lookalike pages and with normal sites for speed and false positives.

## 🟨 Interfaces (deferred)
- Calls: `POST /check`, `GET /scan/{id}`, `GET /blocklist`, `POST /events`, `POST /feedback`.
- Local storage: allowlist, user allowlist, verdict cache, settings, device token.

## 🟨 Done when (deferred; not part of the current definition of done)
- A staged phishing page is warned or blocked before the user can type in it; reason shown.
- A normal site loads with no visible delay; most are resolved locally.
- The event shows in the personal dashboard; false-positive report reaches the admin queue.
- Works in both Chrome and Edge.

## Risks and cut-lines
- Manifest V3 limits: no classic blocking network hook; use tab redirect and (optionally) declarative rules; do not rely on a long-lived worker.
- Broad permissions raise review friction: demo unpacked; state privacy design.
- Google result markup changes often: keep search badges optional.
- Cut-line: Lite mode only; then Form Guard; then badges.

## Time estimate
About 5 hours, 🟨 **not spent now** (deferred).
