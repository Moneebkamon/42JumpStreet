# Real-data findings (2026-11-23)

Numbers: `docs/real-data-eval.md` (rules only) and `docs/real-data-eval-ml.md` (rules + URL model), produced by `scripts/run_real_eval.py`. Link text only, no contact, threat-feed rule off.

## Timeline
1. **First run: 0 of 300 real phishing URLs flagged.** The rules were written for brand-impersonation lures (the golden set, 13 of 14). Real in-the-wild links are mostly random-named pages on free hosting (`pages.dev`), look-alikes of brands outside the UAE list (Roblox), and shorteners.
2. **Changes made, designed from the 150-URL train half only** (`backend/tests/fixtures/openphish_split.json`): a free-hosting rule for machine-generated page names (+30), 18 widely impersonated global brands, and a bundled top-5000 popular-sites list that stops brand false alarms on well-known domains (amazonaws.com, office.net). The check also exposed a pre-existing bug: the `eand` token false-alarmed on words like `timeanddate.com`; tokens can now be explicit and whole-word-only.
3. **Result:** about 57% of the 150 held-out phishing URLs reach "suspicious" (train half: 62%), with about 1% false alarms on 1,000 random mid-popularity sites. Nothing reaches "high risk".

## What is and is not shown
- Shown: the text-only layer improved on data it was not designed from, and most of the 1% false alarms are a brand's own foreign domain (google.so, vodafone.pt), which the allowlist review queue is meant to absorb.
- Not shown: UAE accuracy; accuracy on login/payment pages and small local sites; the false-alarm cost on legitimate free-hosting pages (the new rule's biggest risk; none are in the benign sample); behaviour on next month's kits.
- The free-hosting rule mostly catches one kit family (`xxxxx-xxx-xxxx-xxxxx-DD-MM-YYYY-aa.pages.dev`). Expect it to decay as kits change.
- "Suspicious" (30-59) is a warning band, not a verdict. A 57% figure is detection at that band only.

## Next
Network signals (domain age from the registry, certificate details from public CT logs, DNS via a public resolver, no TLS handshake with the scam server) on the same 300 URLs, then the live certificate reader.
