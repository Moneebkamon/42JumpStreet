"""Evaluate the configured rules against a feature dict. Points come from config/rule_weights.yaml.

A rule whose input feature is missing does not fire, so rules for stages that are not
built yet (domain age, page content) are safe to list here already.
"""


def _num(f: dict, key: str, default: float = 0) -> float:
    v = f.get(key)
    return default if v is None else v


def _known_site_name(f: dict) -> bool:
    """The brand word sits in the registered name of a well-known site (amazonaws.com, office.net): not an impersonation.
    A brand word in a SUBDOMAIN of a popular host (adcb.pages.dev) still counts: free hosts are popular and abused."""
    return bool(_num(f, "url_domain_popular")) and bool(_num(f, "brand_in_domain"))


def _brand(f: dict) -> str:
    return f.get("brand_name") or f.get("brand_page_name") or "a protected brand"


# rule name -> (predicate, reason text)
RULES = {
    "brand_name_not_official_domain": (
        lambda f: _num(f, "brand_impersonation") == 1 and not _known_site_name(f),
        lambda f: f"Uses the name of {_brand(f)} but the domain is not one of its official domains",
    ),
    "brand_typosquat": (
        lambda f: _num(f, "brand_typosquat") == 1 and not _known_site_name(f),
        lambda f: f"Domain is a one-letter variation of {_brand(f)}",
    ),
    "homoglyph_or_punycode": (
        lambda f: _num(f, "url_has_punycode") or _num(f, "url_mixed_script") or _num(f, "url_confusable_chars") > 0,
        lambda f: "Domain uses look-alike or mixed-script characters to imitate another name",
    ),
    "free_host_generated_name": (
        lambda f: _num(f, "url_generated_label") == 1,
        lambda f: "Page name on a free hosting service looks machine-generated (random code groups or a date), a pattern used by phishing kits",
    ),
    "risky_tld": (
        lambda f: _num(f, "url_tld_risk") >= 0.5,
        lambda f: "Domain ending is commonly abused in scams",
    ),
    "suspicious_keywords_2_plus": (
        lambda f: _num(f, "url_suspicious_keywords") >= 2,
        lambda f: "URL contains several pressure or account words (login, verify, secure...)",
    ),
    "url_shortener": (
        lambda f: _num(f, "url_is_shortener") == 1,
        lambda f: "Link goes through a URL shortener that hides the real destination",
    ),
    "ip_host": (
        lambda f: _num(f, "url_is_ip_host") == 1,
        lambda f: "Link uses a raw IP address instead of a domain name",
    ),
    "domain_age_under_7_days": (
        lambda f: f.get("domain_age_days") is not None and f["domain_age_days"] < 7,
        lambda f: f"Domain was registered only {f['domain_age_days']} day(s) ago",
    ),
    "very_new_certificate": (
        lambda f: f.get("tls_cert_age_days") is not None and f["tls_cert_age_days"] < 3,
        lambda f: "Security certificate was issued within the last 3 days",
    ),
    "brand_plus_credential_form": (
        # the domain imitates a brand OR the page presents itself as one, on a domain that is not the brand's
        lambda f: (_num(f, "brand_impersonation") == 1 or _num(f, "brand_page_claim") == 1)
        and _num(f, "content_has_credential_form") == 1,
        lambda f: f"Page imitates {_brand(f)} and asks for a password or payment details",
    ),
    "form_posts_to_other_domain": (
        lambda f: _num(f, "content_form_cross_domain") == 1,
        lambda f: "A form on the page sends its data to a different domain",
    ),
    "urgency_language": (
        lambda f: _num(f, "content_urgency_terms") >= 2,  # two distinct phrases, one alone is too common
        lambda f: "Page uses urgent or threatening language",
    ),
    "guaranteed_returns": (
        lambda f: _num(f, "content_guaranteed_return_terms") >= 1,
        lambda f: "Page promises guaranteed profit or risk-free returns",
    ),
    "hidden_content": (
        lambda f: _num(f, "content_hidden_iframes") > 0 or _num(f, "content_obfuscated_scripts") > 0,
        lambda f: "Page hides content in invisible frames or obfuscated scripts",
    ),
    "redirect_chain_3_plus": (
        lambda f: _num(f, "redirect_hops") >= 3,
        lambda f: "Link bounces through 3 or more redirects",
    ),
    # Ready model, one weak signal (global data, biased by domain ending). Two tiers picked from the held-out check in
    # docs/ready-model-eval.md: >= 0.95 is about 1% false alarms on popular domains, 0.83-0.95 about 5%.
    "ml_url_pattern_strong": (
        lambda f: _num(f, "ml_phish_prob") >= 0.95,
        lambda f: "The link's text closely resembles known phishing links (statistical model, can be wrong)",
    ),
    "ml_url_pattern": (
        lambda f: 0.83 <= _num(f, "ml_phish_prob") < 0.95,
        lambda f: "The link's text somewhat resembles known phishing links (statistical model, can be wrong)",
    ),
    "scam_phone_match": (
        lambda f: _num(f, "content_scam_phone_match") == 1,
        lambda f: "Page shows a phone number linked to known scams",
    ),
}


def evaluate_rules(features: dict, weights: dict | None = None) -> list[dict]:
    """Return the fired rules as [{rule, points, reason}], highest points first.

    `weights` defaults to the effective ones (YAML plus any admin changes); pass others to preview a change."""
    if weights is None:
        from app.engine.scoring.tuning import rule_weights

        weights = rule_weights()
    hits = []
    for name, (predicate, reason) in RULES.items():
        points = weights.get(name)
        if points and predicate(features):
            hits.append({"rule": name, "points": int(points), "reason": reason(features)})
    return sorted(hits, key=lambda h: -h["points"])
