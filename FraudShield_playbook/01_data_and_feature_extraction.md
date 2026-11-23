# Stage 01: Data and Feature Extraction

## Goal
Build a labeled dataset and the analyzers that turn a URL (and later a page) into a feature dictionary. These analyzers are used both for training and for live scoring.

## Depends on
Stage 00.

## Components and their single jobs
| Component | Job | Location |
|---|---|---|
| Feed fetcher | Download phishing and benign URL lists into raw storage | `scripts/fetch_feeds.py`, `data/raw/` |
| Dataset builder | Merge, deduplicate, drop dead/duplicate entries, record source and date | `ml/src/build_dataset.py` |
| Label store | Keep label, source and timestamp for every URL | `ml/src/label_store.py` |
| URL normalizer | One canonical form of a URL (host lowercase, tracking params stripped) | `analyzers/url_analyzer/normalizer.py` |
| Lexical analyzer | Length, dots, hyphens, digits, entropy, keywords, TLD, subdomain depth | `analyzers/url_analyzer/lexical.py` |
| Homoglyph analyzer | Detect lookalike characters and punycode | `analyzers/url_analyzer/homoglyph.py` |
| Shortener detector | Recognize known URL shorteners | `analyzers/url_analyzer/shortener.py` |
| RDAP client | Domain creation date, registrar, privacy flag | `analyzers/domain_intel/rdap_client.py` |
| DNS client | Records, name servers, resolved IP | `analyzers/domain_intel/dns_client.py` |
| TLS client | Certificate issuer and age | `analyzers/domain_intel/tls_client.py` |
| ASN lookup | Hosting network of the IP | `analyzers/domain_intel/asn_lookup.py` |
| Intel cache | Store domain intel so repeated lookups are instant | `analyzers/domain_intel/intel_cache.py` |
| Threat feed loader/lookup | Load known-bad lists and answer "is this listed?" | `analyzers/threat_intel/` |
| Feature assembler | Merge analyzer outputs into one flat vector | `engine/feature_assembler.py` |
| Feature table builder | Run assembler over the dataset and save a table | `ml/src/make_features.py`, `data/processed/` |

## Data sources (verify availability and licence first)
- **Phishing:** OpenPhish community feed, PhishTank, URLhaus, PhishStats.
- **Benign:** Tranco top-sites list, Majestic Million.
- **Ready-made sets for a quick baseline:** UCI Phishing Websites, PhiUSIIL, public Kaggle/Mendeley phishing sets.
- **Your own set (important):** fetch 1-2k live phishing and 1-2k benign pages yourself, including **hard negatives** (small legitimate sites, real bank login pages, brand-new legitimate domains) so the model learns the difference between "new" and "bad".
- Public datasets are stale and biased (phishing from a feed, benign from top sites). Treat them as a starting point, not the truth.

## Tasks
1. Fetch feeds into `data/raw/` and record the download date and source per file.
2. Build the dataset: normalize URLs, remove duplicates, keep only URLs you can use, store label + source + date.
3. Implement URL normalizer and the three URL analyzers; add unit tests with fixture URLs and expected features.
4. Implement domain-intel clients with timeouts and a cache; define what each returns when the lookup fails (explicit "unknown", never a crash).
5. Implement threat-feed loader and lookup.
6. Implement the feature assembler with a documented list of feature names and types (`docs/scoring-spec.md`).
7. Run the feature builder over the dataset (URL and domain features first; content features come in stage 04).
8. Split by **time** (older for training, newer for testing) and write the split rule down.

## Interfaces
- **Input:** a URL string (and optionally page data later).
- **Output:** a flat dictionary of features with stable names, plus a list of which analyzers succeeded (so scoring can report confidence).

## Done when
- A command produces a feature table for at least a few thousand labeled URLs.
- Every analyzer has tests and a defined failure value.
- `docs/scoring-spec.md` lists every feature, its source analyzer and meaning.
- Lookups for 100 URLs complete without unhandled errors.

## Risks and cut-lines
- WHOIS/RDAP rate limits: cache aggressively and lookup only the training subset you need.
- Label noise (dead or reclassified URLs): note label date; re-verify a sample manually.
- Cut-line: skip ASN lookup and cert age first; keep domain age, lexical features and threat-feed lookup.

## Time estimate
About 4 hours (one person on data, one on analyzers).
