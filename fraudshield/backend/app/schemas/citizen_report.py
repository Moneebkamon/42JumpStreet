from pydantic import BaseModel, Field


class CitizenReportCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    note: str = Field(default="", max_length=1000)
    contact: str = Field(default="", max_length=200)
    website: str = ""  # honeypot: real people never see or fill this field
