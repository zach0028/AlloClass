from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    text: str
    config_id: UUID


class ClassifyBatchRequest(BaseModel):
    texts: list[str]
    config_id: UUID


class AxisResultDetail(BaseModel):
    axis_id: str
    axis_name: str
    category_id: str
    category_name: str
    confidence: float = Field(ge=0, le=1)
    vote_count: int | None = None
    all_votes: list[str] | None = None


class ChallengerDetail(BaseModel):
    axis_id: str | None = None
    axis_name: str
    alternative_category: str
    argument: str
    agrees_with_original: bool | None = None
    original_confidence: float = Field(ge=0, le=1)


class ClassificationResponse(BaseModel):
    id: UUID
    config_id: UUID
    input_text: str
    results: list[AxisResultDetail]
    overall_confidence: float = Field(ge=0, le=1)
    was_challenged: bool
    challenger_response: list[ChallengerDetail] | None = None
    model_used: str
    tokens_used: int
    processing_time_ms: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ClassificationListResponse(BaseModel):
    items: list[ClassificationResponse]
    total: int
    page: int
    page_size: int
