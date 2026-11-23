"""Turn selected findings into 2-3 plain sentences with fixed templates. Needs no LLM and cannot invent facts:
every clause comes from a rule that actually fired, or from a recorded override."""

OPENING = {
    "safe": "We found no strong warning signs in this link.",
    "suspicious": "This link has some warning signs, but not enough to call it a scam.",
    "high_risk": "This link has several strong warning signs and is probably a scam.",
    "likely_fraud": "This link looks very likely to be a scam.",
}

ADVICE = {
    "allow": "It looks fine to open, but stay careful with any request for passwords or payments.",
    "monitor": "Be careful: do not enter passwords or payment details unless you are sure of the sender.",
    "warn": "Do not open it or enter any details. If it came in a message, check with the sender another way.",
    "review": "Do not open it or enter any details. Report it so it can be reviewed and taken down.",
}

# rule -> short clause that continues "mainly because ..."
CLAUSES = {
    "brand_name_not_official_domain": "it uses a protected brand's name on a domain that is not the brand's own",
    "brand_typosquat": "the domain is a one-letter variation of a protected brand",
    "homoglyph_or_punycode": "the domain uses look-alike characters to imitate another name",
    "risky_tld": "its domain ending is commonly abused in scams",
    "suspicious_keywords_2_plus": "the address is stuffed with pressure or account words such as login or verify",
    "url_shortener": "it hides its real destination behind a link shortener",
    "ip_host": "it uses a raw IP address instead of a normal domain name",
    "domain_age_under_7_days": "the domain was registered only days ago",
    "very_new_certificate": "its security certificate was issued within the last few days",
    "brand_plus_credential_form": "the page imitates a brand and asks for a password or payment details",
    "form_posts_to_other_domain": "a form on the page sends what you type to a different website",
    "urgency_language": "the page uses urgent or threatening language",
    "guaranteed_returns": "the page promises guaranteed or risk-free profit",
    "hidden_content": "the page hides content in invisible frames or scrambled scripts",
    "redirect_chain_3_plus": "the link bounces through several redirects",
    "ml_url_pattern_strong": "the text of the link closely resembles known phishing links",
    "ml_url_pattern": "the text of the link somewhat resembles known phishing links",
    "scam_phone_match": "the page shows a phone number linked to known scams",
}
ML_RULES = {"ml_url_pattern_strong", "ml_url_pattern"}


def _join(clauses: list[str]) -> str:
    if len(clauses) == 1:
        return clauses[0]
    return ", ".join(clauses[:-1]) + " and " + clauses[-1]


def write(result: dict, findings: list[dict]) -> str:
    band = result.get("band", "safe")
    sentences = [OPENING.get(band, OPENING["safe"])]
    if band == "safe" and any(f.get("rule") != "override" for f in findings):
        sentences = ["Nothing here is strong enough to call this a scam, but there are minor warning signs."]

    overrides = [f for f in findings if f.get("rule") == "override"]
    rules = [f for f in findings if f.get("rule") != "override"]
    parts = []
    for o in overrides:
        text = o["reason"]
        parts.append("it is " + text[0].lower() + text[1:] if text.startswith("Domain is ") else text[0].lower() + text[1:])
    parts += [CLAUSES.get(f["rule"], f["reason"][0].lower() + f["reason"][1:]) for f in rules]
    if parts:
        lead = "Mainly because" if band != "safe" else "Specifically,"
        sentences.append(f"{lead} {_join(parts)}.")
        if rules and all(f["rule"] in ML_RULES for f in rules) and not overrides:
            sentences.append("That statistical resemblance is the only signal, and it is often wrong.")

    sentences.append(ADVICE.get(result.get("action", "allow"), ADVICE["allow"]))

    caveats = []
    if result.get("analyzers_failed"):
        caveats.append("some checks could not run, so this may be incomplete")
    if result.get("page") is None and band != "safe":
        caveats.append("only the link was checked, not the page itself")
    if caveats:
        sentences.append("Note: " + " and ".join(caveats) + ".")
    return " ".join(sentences)
