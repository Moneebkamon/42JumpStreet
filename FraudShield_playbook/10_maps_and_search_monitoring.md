# Stage 10: Maps and Search Monitoring

## Goal
Cover where victims start: verify business listings (Maps) against official brand data, check search results for brand-related queries, and show flagged listings on a geographic map.

## Depends on
Stages 03, 04 (page analysis), `config/brands.yaml` from stage 00.

## Components and their single jobs
| Component | Job | Location |
|---|---|---|
| Listing model/repo | Store checked listings and verdicts | `db/models/listing.py`, `repositories/listing_repo.py` |
| Maps checker | Compare a listing's name, phone, website, category and location to the brand registry | `discovery/maps_checker.py` |
| Search monitor | Run brand-related queries, collect results and ads, score the linked sites | `discovery/search_monitor.py` |
| Listing signals | Duplicate phone across listings, brand name without being an official branch, new listing, review burst | inside `maps_checker` as separate small functions |
| Endpoints | `listings`, `search_monitor` | `api/v1/endpoints/listings.py`, `search_monitor.py` |
| Map page | Geographic fraud map | `src/app/(analyst)/console/map/page.tsx` |
| Map components | Map with markers, listing popup | `components/map/fraud-map.tsx`, `listing-popup.tsx` |
| Sample data | Pre-collected listings for the demo | `data/samples/` |

## Listing verification logic
A listing is suspicious when it claims a brand (name or category) **and** at least one mismatch:
- phone number differs from the brand's official numbers;
- website domain is not official (and then runs through the normal scan);
- address is not one of the brand's known branches;
- same phone appears on several unrelated listings;
- listing is new or reviews arrive in a burst.

Result: a score, reasons and the matched brand; flagged listings link to the scan of their website and can start a case.

## Data and terms (important)
- Use the **official Places API** (quota and cost apply) or a prepared sample set. **Do not scrape Maps.**
- Use an official search API for search monitoring; check its quota and terms.
- Because quotas are limited, the demo should run from a **pre-collected sample set** plus a small live check.

## Tasks
1. Create the listing table and repository.
2. Extend `config/brands.yaml` with official phones and known branch addresses for the demo brands.
3. Implement the maps checker and its signals; unit test each signal.
4. Implement the search monitor: query list per brand, result collection, scoring through the existing pipeline.
5. Add endpoints and the scheduled task for periodic monitoring.
6. Build the map page and components (markers colored by risk, popup with mismatch table).
7. Prepare the sample listing set including one clearly fake branch listing linked to a staged phishing site.

## Interfaces (names only)
- `POST /listings/check`, `GET /listings` (filters: brand, score, area)
- `POST /search-monitor/run`, `GET /search-monitor/results`

## Done when
- The demo shows a fake branch listing flagged with a clear mismatch table and a link to its website scan.
- The map shows flagged listings and filters by brand.
- API usage stays within quota (cached, batched).

## Risks and cut-lines
- API quotas and cost: cache results; use samples for rehearsal.
- Terms of service: official APIs only.
- Cut-line: skip live search monitoring first; keep one Maps scenario end to end.

## Time estimate
About 3-4 hours.
