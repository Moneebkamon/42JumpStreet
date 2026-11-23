# Pitch notes (about 3 minutes)

## One sentence
FraudShield checks a suspicious link before you open it, explains why in plain words, and gives analysts a path from detection to a documented takedown report.

## Structure
1. **Problem (30 s).** Scam links arrive by SMS, search results and fake map listings, and impersonate UAE banks, government services and delivery firms. People decide in seconds; takedowns take days and need evidence.
2. **What it does (60 s).** Paste a link, get a score and the reasons, no account needed. It reads the address, checks the domain's age and certificate, looks the link up in a public phishing feed, and lets signed-in staff open a page in an isolated browser (demo: staged pages only) to spot fake login forms. Analysts triage a queue, open cases, freeze hashed evidence, and prepare takedown drafts that always say "suspected" until a person confirms.
3. **How it is built (30 s).** Explainable rules plus a small ready-made URL model, so each warning has a reason. Humans decide: nothing is sent or blocked automatically. Staff roles, an audit log, and a hardened container setup.
4. **What we can honestly claim (30 s).**
   - It works end to end and is tested (180 automated tests, a browser run of the whole flow, containers verified).
   - It is explainable: every score shows its reasons.
   - It is designed for human review: reasons required, evidence hashed, audit trail.
5. **Ask / next (30 s).** Real certificate stream and UAE-labelled data to measure accuracy; partner feeds; takedown channels.

## Scope statement (say it)
This is a demo build. The safe-browser deep scan is for staff and for staged test pages only; it is not ready for real scam pages. Early-detection data is simulated.

## Claims to avoid
- "Detects unknown scams." Threat feeds only cover scams already caught; say "adapts as new labelled cases arrive" and only after it does.
- Any accuracy figure from `docs/golden-report.md` or `docs/ready-model-eval.md`: they are small development checks (the rules were tuned by the same person who wrote the test set; the model eval used easy negatives).
- "Real-time monitoring" of certificates: the demo feed is a **simulated** sample.
- "Takedown automation": it drafts text only.

## If asked
- *How accurate is it on real phishing?* "On 150 real phishing URLs we had not designed against (OpenPhish, global), the link text alone reaches 'suspicious' for about 57%, with under 1% false alarms on 1,000 ordinary sites. It is one signal; domain age, certificates, feeds and page analysis add to it. Not measured: UAE-specific links, login pages, legitimate free-hosting pages." Details: `docs/real-data-findings.md`.
- *How accurate is it on lures like ours?* "We have not measured accuracy on real UAE data yet. On our small hand-labelled check it flagged 13 of 14 phishing-style links with one false alarm out of 18 legitimate ones, but that set is ours, so please read it as a development check."
- *Why not machine learning only?* "A small model is included, but alone it could not reach 'suspicious' on held-out phishing and it is biased by domain ending. Rules give reasons a person can check."
- *Privacy?* "Scans are stored for the history page; citizen reports hold only what the person typed; scanned links travel in the request body, so they are not in the web access log. A full privacy review is not done yet (`docs/privacy-design.md` is still an empty placeholder)."
