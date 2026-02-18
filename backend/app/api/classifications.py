from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.classification_result import ClassificationResult
from app.schemas.classification import ClassificationListResponse, ClassificationResponse

router = APIRouter(prefix="/api/classifications", tags=["Database Explorer"])


@router.get("", response_model=ClassificationListResponse)
async def list_classifications(
    config_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    min_confidence: float | None = Query(default=None, ge=0, le=1),
    max_confidence: float | None = Query(default=None, ge=0, le=1),
    was_challenged: bool | None = None,
    search: str | None = Query(default=None, max_length=200),
    db: AsyncSession = Depends(get_db),
):
    base_filter = ClassificationResult.config_id == config_id

    query = select(ClassificationResult).where(base_filter)
    count_query = (
        select(func.count())
        .select_from(ClassificationResult)
        .where(base_filter)
    )

    if search:
        search_filter = ClassificationResult.input_text.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if min_confidence is not None:
        query = query.where(ClassificationResult.overall_confidence >= min_confidence)
        count_query = count_query.where(ClassificationResult.overall_confidence >= min_confidence)
    if max_confidence is not None:
        query = query.where(ClassificationResult.overall_confidence <= max_confidence)
        count_query = count_query.where(ClassificationResult.overall_confidence <= max_confidence)
    if was_challenged is not None:
        query = query.where(ClassificationResult.was_challenged == was_challenged)
        count_query = count_query.where(ClassificationResult.was_challenged == was_challenged)

    total = (await db.execute(count_query)).scalar() or 0

    query = (
        query
        .order_by(ClassificationResult.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    items = list(result.scalars().all())

    return ClassificationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{classification_id}", response_model=ClassificationResponse)
async def get_classification(
    classification_id: UUID, db: AsyncSession = Depends(get_db)
):
    classification = await db.get(ClassificationResult, classification_id)
    if classification is None:
        raise HTTPException(status_code=404, detail="Classification non trouvee")
    return classification
