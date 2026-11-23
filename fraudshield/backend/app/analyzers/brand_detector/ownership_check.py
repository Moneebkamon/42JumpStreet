"""Is this host really one of a brand's official domains?"""
from app.analyzers.brand_detector.registry import Brand, get_brands


def is_official(host: str, brand: Brand) -> bool:
    host = host.lower()
    return any(host == d or host.endswith("." + d) for d in brand.official_domains)


def official_brand(host: str) -> Brand | None:
    """Return the brand that owns this host, or None."""
    for brand in get_brands():
        if is_official(host, brand):
            return brand
    return None
