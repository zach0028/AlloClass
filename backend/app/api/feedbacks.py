from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user_feedback import UserFeedback
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, SuggestionResponse
from app.services.error_pattern_detector import generate_suggestions
from app.services.feedback_learning import store_feedback

router = APIRouter(prefix="/api/feedbacks", tags=["Feedbacks"])


@router.post("", response_model=FeedbackResponse, status_code=201)
async def create_feedback(
    request: FeedbackCreate, db: AsyncSession = Depends(get_db)
):
    feedback = await store_feedback(
        classification_id=request.classification_id,
        axis_id=request.axis_id,
        corrected_category_id=request.corrected_category_id,
        reasoning_feedback=request.reasoning_feedback,
        feedback_type=request.feedback_type,
        db=db,
    )
    return feedback


@router.get("/classification/{classification_id}", response_model=list[FeedbackResponse])
async def get_feedbacks_for_classification(
    classification_id: UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserFeedback).where(UserFeedback.classification_id == classification_id)
    )
    return list(result.scalars().all())


@router.get("/suggestions", response_model=list[SuggestionResponse])
async def get_suggestions(config_id: UUID, db: AsyncSession = Depends(get_db)):
    raw_suggestions = await generate_suggestions(config_id, db)
    return [SuggestionResponse(**s) for s in raw_suggestions]
