# Stage 02: Model and Scoring Engine

## Goal
Train a fast model and a fuller model, define the rule layer, and produce a calibrated 0-100 Fraud Risk Score with a band, a confidence and the top reasons.

## Depends on
Stage 01 (features and dataset).

## Components and their single jobs
| Component | Job | Location |
|---|---|---|
| Trainer | Train the fast model (URL + domain features) and the full model (adds content features later) | `ml/src/train.py` |
| Evaluator | Time-split metrics, false-positive report on benign hard negatives | `ml/src/evaluate.py` |
| Calibrator | Calibrate probabilities and choose the threshold at high precision | `ml/src/calibrate.py` |
| Exporter | Write a versioned model artifact with metadata (features, date, metrics) | `ml/src/export_model.py`, `ml/artifacts/` |
| Model loader | Load the chosen artifact version at startup | `backend/app/ml/model_loader.py` |
| Predictor | Run fast or full inference on a feature vector | `backend/app/ml/predictor.py` |
| SHAP explainer | Return the top contributing features per prediction | `backend/app/ml/shap_explainer.py` |
| Rule engine | Evaluate configured rules and sum their points | `engine/scoring/rules.py`, `config/rule_weights.yaml` |
| Combiner | Merge ML score and rule points into the final score | `engine/scoring/combiner.py` |
| Overrides | Allowlist cap and threat-feed floor | `engine/scoring/overrides.py` |
| Bands | Map score to label and action using config | `engine/scoring/bands.py`, `config/risk_bands.yaml` |

## Scoring design (summary; details go in `docs/scoring-spec.md`)
- **ML score:** model probability scaled to 0-100.
- **Rule points:** triggered rules add configured points (capped at 100). Examples: domain under 7 days, brand + credential form, form posts to another domain, homoglyph, very new certificate, risky TLD, urgency language, redirect chain of 3+ hops, scam phone match. Weights are starting values; tune on your data.
- **Final score:** weighted blend of ML score and rule points.
- **Overrides:** confirmed in a threat feed raises the floor to high; allowlisted or official domains are capped low.
- **Bands:** 0-29 safe, 30-59 suspicious, 60-79 high risk, 80-100 likely fraud (stored in config, not code).
- **Confidence:** how many analyzers completed successfully; shown beside the score.
- **Block rule:** block only with a high score **and** two independent signal families, or a confirmed feed hit. ML alone never blocks.

## Build order (2-day plan)
- **Required first:** rules engine, combiner, overrides and bands, reading from `config/`. This alone gives a working, explainable score.
- **Optional, only after the scanner works end to end:** the ML model (needs a few thousand labeled URLs including benign hard negatives). If skipped, say so honestly in the pitch.
- Keep feature extraction in one place so the model can be added later without rewriting the rules.

## Model choices
- **MVP:** XGBoost (or LightGBM) on tabular features; fast, accurate, supports SHAP.
- Keep a logistic-regression baseline for comparison.
- 🟥 **[OUT OF SCOPE]** Transformers and CLIP/embedding models.
- Two models: **fast** (cheap features only; used for discovery pre-scoring and quick scan results; 🟨 the extension `/check` path is deferred) and **full** (adds content, brand and perceptual-hash features, used for deep scans).

## Tasks
1. Train the baseline and the XGBoost fast model on URL + domain features.
2. Evaluate on the time-based test split; report precision, recall and false-positive rate on benign hard negatives separately.
3. Calibrate and pick the operating threshold for high precision.
4. Export versioned artifacts with a metadata file (feature list, training date, metrics).
5. Implement loader and predictor in the backend; confirm the feature order matches the metadata.
6. Implement rules, combiner, overrides and bands reading from `config/`.
7. Write a golden-set test: 30 URLs (phishing, benign, hard negatives) with expected bands.
8. Document the scoring spec.

## Interfaces
- **Input:** feature dictionary (+ list of completed analyzers).
- **Output:** `score` (0-100), `band`, `verdict` (allow / warn / block), `confidence`, `top_features`, `triggered_rules`.

## Done when
- The scoring engine returns score, band, confidence and reasons for any feature dictionary.
- Golden-set test passes; false-positive rate on hard negatives is measured and written down.
- Changing a rule weight or threshold in `config/` changes behavior without a code change.

## Risks and cut-lines
- Inflated accuracy from random splits: use the time split only for reported numbers.
- Overfitting to dataset quirks: check that "domain age" is not the only thing the model learned.
- Cut-line: skip calibration plots and SHAP at first; keep rules + model + bands. Add SHAP before the demo for the explanation panel.

## Time estimate
About 4 hours.
