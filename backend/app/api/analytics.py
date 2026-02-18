from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.analytics import (
    AxisStatsResponse,
    ClassificationMatrixResponse,
    ConfidenceBucket,
    ConfidenceResponse,
    EmbeddingMapResponse,
    KPIResponse,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/kpis", response_model=KPIResponse)
async def get_kpis(config_id: UUID, db: AsyncSession = Depends(get_db)):
    from app.services.analytics_computation import compute_kpis

    result = await compute_kpis(config_id, db)
    return KPIResponse(**result)


@router.get("/confidence", response_model=ConfidenceResponse)
async def get_confidence_distribution(
    config_id: UUID, db: AsyncSession = Depends(get_db)
):
    from app.services.analytics_computation import compute_confidence_distribution

    result = await compute_confidence_distribution(config_id, db)
    return ConfidenceResponse(
        buckets=[
            ConfidenceBucket(
                range_start=i * 0.1,
                range_end=(i + 1) * 0.1,
                count=b["count"],
            )
            for i, b in enumerate(result)
        ]
    )


@router.get("/axes", response_model=list[AxisStatsResponse])
async def get_axes_stats(config_id: UUID, db: AsyncSession = Depends(get_db)):
    from app.services.analytics_computation import compute_axes_stats
    from app.services.config_management import get_config_with_relations

    config = await get_config_with_relations(config_id, db)
    name_to_id = {axis.name: axis.id for axis in config.axes}

    stats = await compute_axes_stats(config_id, db)
    results = []
    for s in stats:
        axis_name = s["axis_name"]
        axis_id = name_to_id.get(axis_name)
        if axis_id is None:
            continue

        top_cats = s.get("top_categories", [])
        most_confused = None
        if len(top_cats) >= 2:
            most_confused = [top_cats[0]["name"], top_cats[1]["name"]]

        cat_dist = {c["name"]: c["count"] for c in top_cats}

        results.append(AxisStatsResponse(
            axis_id=axis_id,
            axis_name=axis_name,
            accuracy=s["accuracy"] if s["accuracy"] is not None else 0.0,
            most_confused_pair=most_confused,
            category_distribution=cat_dist,
        ))
    return results


@router.get("/embeddings", response_model=EmbeddingMapResponse)
async def get_embedding_map(config_id: UUID, db: AsyncSession = Depends(get_db)):
    from app.services.analytics_computation import compute_embedding_map

    result = await compute_embedding_map(config_id, db)
    return EmbeddingMapResponse(points=result)


@router.get("/classification-matrix", response_model=ClassificationMatrixResponse)
async def get_classification_matrix(
    config_id: UUID,
    x_axis: str | None = None,
    y_axis: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    from app.services.analytics_computation import compute_classification_matrix

    result = await compute_classification_matrix(config_id, db, x_axis, y_axis)
    return ClassificationMatrixResponse(**result)
