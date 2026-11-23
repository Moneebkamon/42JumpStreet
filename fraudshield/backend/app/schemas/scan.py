from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    deep: bool = False  # also open the page in the sandbox browser (slower)


class Reason(BaseModel):
    rule: str
    points: int
    reason: str


class ScanResponse(BaseModel):
    scan_id: str
    state: str  # queued | running | complete | failed (only "complete" for now)
    url: str
    score: int
    band: str
    action: str
    confidence: float
    reasons: list[Reason]
    analyzers_ok: list[str]
    analyzers_failed: list[str]
    features: dict
    explanation: str = ""  # 2-3 plain sentences built from the findings that fired
    page: dict | None = None  # what the sandbox saw; None unless deep
    cached: bool = False  # True when answered from a result proactive discovery computed earlier


class StoredScan(ScanResponse):
    created_at: str
    feedback: str | None = None  # human verdict: "scam" | "safe"


class ScanSummary(BaseModel):
    scan_id: str
    url: str
    score: int
    band: str
    action: str
    deep: bool
    cached: bool
    created_at: str
    feedback: str | None = None


class FeedbackRequest(BaseModel):
    label: str = Field(pattern="^(scam|safe)$")
