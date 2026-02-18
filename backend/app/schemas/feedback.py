from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    classification_id: UUID
    axis_id: UUID
    corrected_category_id: UUID | None = None
    reasoning_feedback: str | None = None
    feedback_type: Literal["validated", "corrected", "nuanced"]


class FeedbackResponse(BaseModel):
    id: UUID
    classification_id: UUID
    axis_id: UUID
    corrected_category_id: UUID | None
    original_category_id: UUID | None
    reasoning_feedback: str | None
    feedback_type: Literal["validated", "corrected", "nuanced"]
    review_status: Literal["corrected", "validated", "non_reviewed"]
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SuggestionResponse(BaseModel):
    type: str
    message: str
    axis_id: UUID | None = None
    details: dict | None = None
