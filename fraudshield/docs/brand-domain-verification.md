# Brand official-domain check (2026-11-23)

`config/brands.yaml` `official_domains` decide which hosts count as the brand's own (never flagged as impersonation).
They were first written from memory. This is a web-search check (search results only, no site opened), so it is
evidence, not proof. A wrong entry is dangerous in one direction: a scam domain listed as official is never flagged.

| Brand | Domain in the file | Result |
|---|---|---|
| ADCB | adcb.com | Confirmed (bank's own pages). Whether `adcb.ae` is also owned is **not confirmed**, so it stays unlisted and scores as a lookalike. |
| FAB | bankfab.com | Confirmed (site terms say it is owned by First Abu Dhabi Bank PJSC). |
| Emirates NBD | emiratesnbd.com | Confirmed. |
| ADIB | adib.ae | Confirmed by a government directory and the bank's own `/en/about` page appearing in results. |
| DIB | dib.ae | Listed on a Dubai Land Department page; no independent directory. Likely right. |
| Abu Dhabi Police | adpolice.gov.ae | Confirmed (GHQ site and service pages). |
| ICP | icp.gov.ae | Confirmed (the page itself warns about fake sites using its name). |
| MOI | moi.gov.ae | Not confirmed from the site itself; a third-party guide quotes `@moi.gov.ae` mail. Likely right. |
| e& / Etisalat | etisalat.ae, eand.com | Both confirmed. |
| TAMM | tamm.abudhabi | **Not confirmed**: the search did not return the site. Operator is the Department of Government Enablement. Check by hand. |
| Salik | salik.gov.ae | **Not confirmed**: nothing returned. The real site may be `salik.ae`; check by hand before changing. |
| Microsoft | microsoft-int.com | **Added from memory, not confirmed.** The live stream shows many `*.fabric.microsoft-int.com` hosts that look like Microsoft internal names, but ownership was not verified. If it is wrong, remove it. |
| (not listed) | mcas.ms | Microsoft's docs confirm it is the Defender for Cloud Apps proxy suffix (`netflix.com.mcas.ms`). **Deliberately NOT allowlisted:** other organisations' traffic is proxied through it, and Microsoft itself says to block unrecognised mcas.ms URLs. Expect these as noise. |
| (not listed) | microsoft-falcon.net | Not found in the search. Not allowlisted. |
| Global brands (Google, Amazon, PayPal, etc.) | see file | Not checked in this pass. |

## To do by a person
1. Open the real TAMM and Salik sites from the official apps or a government portal link (u.ae) and confirm the domains.
2. Ask the banks, or check the UAE Central Bank list, whether `adcb.ae` and similar `.ae` redirects are owned.
3. Check `microsoft-int.com` ownership with a registry lookup (WHOIS or RDAP) and decide whether to keep it.
