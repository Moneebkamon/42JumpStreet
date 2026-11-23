"""False alarms seen on the live certificate stream must not match a brand; real lookalikes still must."""
import pytest

from app.analyzers.url_analyzer.normalizer import normalize
from app.analyzers.brand_detector.name_matcher import find_brand_match
from app.discovery.prefilter import prefilter


def _brand(host: str):
    m = find_brand_match(normalize(host))
    return m.brand.id if m else None


@pytest.mark.parametrize("host", [
    "qponwww.ihgnidcbadcbdilemascontemporaneoseducacionpoliticayvalores.com.updays.site",  # brand inside a long junk label
    "finance.truecast.ca",            # "finance" is a word, not a typo of binance
    "tammywells.net",                 # first name
    "ppgym.demo.ladibay.com",         # short token in the middle of a label
    "moi.hoalacanh.id.vn",            # very short name in a subdomain
    "z91.w.api.fabric.microsoft-int.com",  # Microsoft's own internal domain
])
def test_known_false_alarms_do_not_match(host):
    assert not prefilter(host).keep or _brand(host) is None


@pytest.mark.parametrize("host,brand", [
    ("padpal.ai", "paypal"),
    ("login.microsogt.com", "microsoft"),
    ("metamsk-login-docs.pages.dev", "metamask"),
    ("adcb-login.xyz", "adcb"),
    ("secure-adcbbank.com", "adcb"),
    ("mwww.fabebook.com", "facebook"),
])
def test_real_lookalikes_still_match(host, brand):
    assert _brand(host) == brand
    assert prefilter(host).keep
