from pydantic import BaseModel

from app.schemas.scan import Reason


class FeedItem(BaseModel):
    domain: str
    source: str
    simulated: bool
    issued_at: str
    detected_at: str
    issue_to_detection_s: float
    processing_ms: float
    score: int
    band: str
    action: str
    brand_id: str
    brand_name: str
    prefilter_reasons: list[str]
    reasons: list[Reason]
    status: str


class BrandCount(BaseModel):
    brand_id: str
    brand_name: str
    count: int


class CheckedItem(BaseModel):
    domain: str
    checked_at: str
    source: str
    simulated: bool
    kept: bool  # False: the cheap name check found no brand or scam wording, so it was not scored
    score: int | None = None
    band: str = ""  # safe | suspicious | high_risk | likely_fraud | known (scored earlier) | "" (not scored)
    brand_name: str = ""


class DiscoveryStats(BaseModel):
    events_processed: int
    domains_seen: int
    domains_kept: int
    pass_through_rate: float
    detections: int
    flagged: int
    avg_processing_ms: float
    avg_issue_to_detection_s: float
    by_band: dict[str, int]
    top_brands: list[BrandCount]
    simulated: bool
    live_events: int = 0  # certificates read from a live stream (0 until the ct-listener has run)
    last_live_run_at: str | None = None  # heartbeat: the listener records a run every ~20 s while connected
    last_live_detection_at: str | None = None


class TriageItem(FeedItem):
    priority: float
    est_cost_s: float
