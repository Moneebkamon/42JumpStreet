# Ready model vs our rules: first held-out check (2026-11-23)

Model: `CrabInHoney/urlbert-tiny-v2-phishing-classifier` (MIT, 3.7M parameters, URL text only).
Run with `ml/build_eval_set.py` -> `ml/score_with_model.py` -> `ml/report.py`. Nothing was fetched or opened; URLs were
only parsed and scored as text.

## Test set
- Phish: 300 URLs from the OpenPhish community feed (loaded 2026-11-23, so newer than the model's training data).
- Good: 400 domains from the Tranco top-1M, seeded sample (200 popular, rank <= 10k; 200 long tail).
- "host" variant cuts each phish URL to scheme + host (fair: negatives are bare domains). "full" keeps the path, which
  lets any scorer cheat on length and path.
- The rules ran with the threat-feed lookup turned off (otherwise every phish scores 85 by lookup) and with no network, so
  the domain-age and certificate signals the rules use in real scans were absent.

## Results (phish "host" vs all 400 good domains)
| Scorer | AUC | What it catches at a practical setting |
|---|---|---|
| Rules (offline) | 0.51 (chance) | 0% at score >= 30; 289 of 300 phish score exactly 0 |
| Model, scheme removed | 0.90 | 63% of phish at 5% false alarms; 38% at 1%; 73% at 10% |
| Model, URL as given (with `https://`) | 0.85 | Unusable at 0.5: 84% of good domains flagged |
| Plain average rules + model | 0.90 | no better than the model alone |

The model must be fed the URL **without** the scheme.

## How to read this (honest limits)
- **Rules scored chance here because of what this feed is, not proof they are bad.** They look for 17 UAE brands and
  keyword patterns; OpenPhish is mostly global phishing on other brands and on compromised sites, and the offline run
  lacks domain age. They have not been measured on UAE-targeted phishing because we have none.
- **The model is global and has a TLD bias.** Its worst false alarms on good domains are mostly `.ru` and `.cn` sites.
  How it treats `.ae` is not measured.
- **Good domains here are popular sites, which are easy.** Real traffic has harder legitimate sites, so real false-alarm
  rates will be higher than these.
- **Small sample** (300 phish). Differences of a few points are noise. Phish from one feed only.
- **Our own reimplementation.** `transformers` cannot load on this machine (its `regex` dependency is blocked by Windows
  Application Control), so `ml/tiny_bert.py` runs the BERT in plain torch. An AUC of 0.90 shows it works, but it was not
  compared against the reference implementation, so tiny numeric differences are possible.
- Do not quote these figures as product accuracy.

## What it means
The model sees global phishing patterns the rules do not, so it is worth keeping as **one extra signal**. It is too
false-alarm-prone and too TLD-biased to decide anything alone. The rules, the model and the threat feed should be blended
by the cost-based layer, with thresholds chosen from data that includes UAE cases.

## After wiring it into the scorer (same day)
The model now runs inside the app (numpy, no torch) and adds two small rules: `ml_url_pattern_strong` (+15 when the
probability is >= 0.95, about 1% false alarms on the popular domains) and `ml_url_pattern` (+8 for 0.83 to 0.95, about 5%).
The numpy version matches the torch reference to within 0.000001 on 12 fixed URLs (a test checks this).

Same held-out set, now scored by the whole rule engine (still offline, no domain age):
| Score threshold | Phish caught | Good domains flagged |
|---|---|---|
| >= 8 | 65% | 6.0% |
| >= 15 | 40% | 2.5% |
| >= 30 ("suspicious") | 0 to 1% | 0.0% |

Integrated AUC is 0.80, below the model alone (0.90), because the two fixed weights squash its output into two tiers.
**By design the model alone cannot push a link into "suspicious"**: it adds a reason line and a few points. So today it
changes what users read much more than the band they see. Raising the weights would catch more phish and flag more good
sites, and the TLD bias (.ru, .cn) would show up in the product. That choice should wait for UAE-relevant data and the
network signals (domain age, certificate) that this offline run lacked.

A bug caught on the way: the model's `tokenizer.json` pads to 64 tokens, and the first numpy version attended to the
padding. The parity test against torch exposed it (the evaluation above was never affected; torch used a proper mask).
