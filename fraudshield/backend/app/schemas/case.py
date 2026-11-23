from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    source: str = Field(pattern="^(scan|detection|report)$")
    source_ref: str = Field(min_length=1, max_length=2048)
    title: str | None = Field(default=None, max_length=200)


class StatusChange(BaseModel):
    to_status: str = Field(min_length=1, max_length=40)
    reason: str = Field(max_length=1000)


class NoteCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
