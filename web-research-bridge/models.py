from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    task: str = Field(..., min_length=3)
    max_results: int | None = None
    max_chars_per_page: int | None = None
