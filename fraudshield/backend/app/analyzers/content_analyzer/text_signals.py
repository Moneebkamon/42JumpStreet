"""Pressure and 'guaranteed profit' language, English and Arabic. Keys start with content_.

Counts DISTINCT phrases, so one repeated word cannot trigger a signal on its own.
"""
from app.analyzers.content_analyzer.page_doc import PageDoc
from app.analyzers.url_analyzer.normalizer import NormalizedURL

URGENCY_TERMS = (
    "account will be suspended", "account has been suspended", "account will be closed", "within 24 hours",
    "verify your account", "verify your identity", "confirm your identity", "unusual activity",
    "final notice", "act now", "immediate action", "your account is locked", "limited time",
    "traffic fine", "pay your fine",
    "عاجل", "تم تعليق", "سيتم إيقاف", "سيتم تعليق", "خلال 24 ساعة", "تأكيد هويتك", "تحقق من حسابك",
    "غرامة مرورية",
)
GUARANTEED_RETURN_TERMS = (
    "guaranteed return", "guaranteed profit", "guaranteed income", "risk-free", "risk free",
    "double your", "daily profit", "passive income",
    "أرباح مضمونة", "عوائد مضمونة", "ربح مضمون", "بدون مخاطر",
)


def _count(text: str, terms: tuple[str, ...]) -> int:
    low = text.lower()
    return sum(term in low for term in terms)


def text_features(doc: PageDoc, n: NormalizedURL) -> dict:
    text = f"{doc.title} {doc.text}"
    return {
        "content_urgency_terms": _count(text, URGENCY_TERMS),
        "content_guaranteed_return_terms": _count(text, GUARANTEED_RETURN_TERMS),
    }
