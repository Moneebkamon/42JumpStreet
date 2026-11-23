# Stage 11: Clustering, AI Explanations and Alerts

## Goal
Link sites into campaigns, turn technical findings into plain-language explanations, and notify people when high-risk detections appear.

## Depends on
Stages 02, 04, 08 (scored detections and extracted contacts).

## Components and their single jobs
| Component | Job | Location |
|---|---|---|
| Fingerprints | Compute template hash, form signature, shared IDs (analytics, wallets, phones, handles) | `clustering/fingerprints.py` |
| Graph builder | Build nodes (sites, numbers, wallets, hosts) and edges (shared attribute) | `clustering/graph_builder.py` |
| Campaign service | Group connected sites into a named campaign with first/last seen | `clustering/campaign_service.py` |
| Campaign model/repo | Store campaigns and membership | `db/models/campaign.py`, `repositories/campaign_repo.py` |
| Cluster task | Periodic clustering job | `workers/tasks/cluster_tasks.py` |
| Campaign endpoint | List campaigns and graph data | `api/v1/endpoints/campaigns.py` |
| Campaign graph UI | Interactive graph; click a node for the site detail | `components/graph/campaign-graph.tsx`, `console/campaigns/[id]/page.tsx` |
| Evidence selector | Pick the 3-5 most important findings for an explanation | `engine/explainer/evidence_selector.py` |
| Explanation writer | Turn structured findings into 2-3 plain sentences | `engine/explainer/llm_client.py` |
| Fallback templates | Template sentences when no LLM is available | `engine/explainer/fallback_templates.py` |
| Alert dispatcher | Decide channel by severity and deliver once | `alerts/dispatcher.py` |
| Channels | Telegram; 🟥 email and webhook **[OUT OF SCOPE]** | `alerts/telegram.py` (🟥 `email.py`, `webhook.py` not built) |
| Alert task | Send alerts asynchronously and de-duplicate | `workers/tasks/alert_tasks.py` |

## Explanation rules
- The explainer receives **only structured findings** (reasons, evidence fields), never raw page text, so a malicious page cannot instruct the model.
- Output must mention only facts present in the findings; no accusations about individuals.
- Always provide the fallback template version; the LLM is an enhancement, not a dependency.
- Same explanation style for the user warning, the analyst case and the takedown draft, in English and Arabic.

## Clustering rules
- Link on strong shared attributes only (same template hash, same form signature, same wallet/phone/analytics ID, same hosting plus registration pattern); weak links (same big hosting provider) are not enough.
- Show **why** two sites are linked.
- Campaign actions (bulk case creation) are advanced; MVP is view-only.

## Alerts rules
- Alert only above a configured threshold; de-duplicate per host and per campaign; include score, brand, reasons and a link to the case.
- Telegram only (fastest to demo). 🟥 **[OUT OF SCOPE]:** email and webhook channels.

## Tasks
1. Implement fingerprint extraction from existing page analysis output.
2. Implement graph builder and campaign service; add the periodic task.
3. Add campaign endpoints and the graph UI.
4. Implement the evidence selector and fallback templates; test explanation quality on 10 detections.
5. Add the LLM writer with strict input limits and a timeout; fall back to templates on failure.
6. Implement alert dispatcher and Telegram channel; add de-duplication.
7. Seed one multi-site campaign for the demo (staged pages sharing a template).

## Interfaces (names only)
- `GET /campaigns`, `GET /campaigns/{id}`
- Alert payload: host, score, band, brand, reasons, case link.

## Done when
- A campaign of several staged sites is shown as one graph with the shared attributes named.
- Every result page shows a readable explanation; works without the LLM.
- A high-risk detection sends exactly one alert to Telegram.

## Risks and cut-lines
- Weak links creating false clusters: use strong attributes only.
- Prompt injection from page text: pass structured data only.
- 🟥 **[OUT OF SCOPE]:** email/webhook alerts. Cut-line for the rest: skip bulk case creation; keep graph, templates, Telegram.
- 🟨 **[EXTENSION - DEFERRED]:** the explanation style for the extension block/warning page; the explainer itself is still built for the result page, case and takedown draft.

## Time estimate
About 3-4 hours.
