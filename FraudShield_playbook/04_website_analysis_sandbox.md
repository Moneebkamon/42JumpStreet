# Stage 04: Website Analysis and Sandbox

## Goal
Fetch suspicious pages safely, extract content signals, detect brand impersonation and redirect behavior, and feed these into the full model and rules.

## Depends on
Stages 01-03.

## Components and their single jobs
| Component | Job | Location |
|---|---|---|
| Sandbox image | Isolated headless browser: no secrets, restricted network, non-root | `infra/docker/sandbox.Dockerfile` |
| Browser pool | Manage a small number of browser instances | `sandbox/browser_pool.py` |
| Fetcher | Load a URL with limits; return final URL, redirect chain, DOM, forms, network targets | `sandbox/fetcher.py` |
| Screenshot | Capture a full-page image | `sandbox/screenshot.py` |
| Policies | Timeouts, size caps, blocked resource types, no downloads | `sandbox/policies.py` |
| Redirect tracer | Record the redirect chain and flag shorteners plus new final domain | `analyzers/redirect_tracer/tracer.py` |
| Form inspector | Password/payment fields, form action domain vs page domain | `analyzers/content_analyzer/form_inspector.py` |
| Text signals | Urgency, guaranteed-return and fake-regulator language, language mismatch | `analyzers/content_analyzer/text_signals.py` |
| Resource ratio | External resources, hidden iframes, obfuscated scripts | `analyzers/content_analyzer/resource_ratio.py` |
| Contact extractor | Phone numbers, wallet addresses, messaging handles | `analyzers/content_analyzer/contact_extractor.py` |
| Brand registry | Load brand data from `config/brands.yaml` | `analyzers/brand_detector/registry.py` |
| Name matcher | Brand name or near-variant in domain, title, text | `analyzers/brand_detector/name_matcher.py` |
| Ownership check | Is the domain actually one of the brand's official domains? | `analyzers/brand_detector/ownership_check.py` |
| Visual match | Screenshot/logo hash similarity to brand references | `analyzers/brand_detector/visual_match.py` |
| Cloaking detector | Compare responses across user agents / device types | `analyzers/cloaking_detector/detector.py` |

## Impersonation rule (implement exactly as three parts)
Impersonation is flagged when **all three** hold: the page claims a brand (name or visual match), the domain is **not** in that brand's official list, **and** the page captures credentials or payment. This keeps false positives low.

## Security rules for the sandbox (important)
- Runs in its own container with no access to secrets or the internal network.
- Fixed time and size limits; downloads disabled; never submit forms; never enter real credentials.
- Fetch with a neutral profile; treat everything fetched as hostile data.
- Store only what you need: screenshot, DOM snapshot, form summary, network targets.

## Tasks
1. Build the sandbox image and confirm it runs a page load with limits.
2. Implement browser pool, fetcher, screenshot and policies.
3. Implement redirect tracer and cloaking detector.
4. Implement form inspector, text signals, resource ratio and contact extractor.
5. Implement the brand registry, name matcher, ownership check; add visual match last (perceptual hash only; 🟥 **[OUT OF SCOPE]** embeddings/CLIP).
6. Extend the feature assembler with content/brand features; retrain the full model (stage 02 scripts).
7. Add tests using your own staged pages in `data/samples/` (a staged lookalike bank page, a staged investment page, a real-looking benign page).
8. Wire the new analyzers into the deep-scan path of the pipeline.

## Interfaces
- **Input:** URL.
- **Output:** content, brand, redirect and cloaking features; screenshot and DOM snapshot references; extracted phone/wallet/handle lists.

## Done when
- A staged lookalike page is flagged as impersonation with an explanation of which parts of the rule matched.
- A legitimate page with a login form on its own official domain is not flagged.
- Deep scan returns within a set time budget (measure it) or returns a partial result.

## Risks and cut-lines
- Sandbox escape or abuse: keep it isolated; no real credentials; strict limits.
- Cloaked pages: compare multiple profiles; note it as a signal, not proof.
- Cut-line: skip visual match and cloaking first; keep forms, name/ownership check and redirects.

## Time estimate
About 4 hours.
