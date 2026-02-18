import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db

router = APIRouter(prefix="/api/evaluate", tags=["Evaluation"])


class GroundTruthRequest(BaseModel):
    config_id: UUID
    ticket_count: int = Field(default=5, gt=0, le=100)
    max_rounds: int | None = Field(default=5, gt=0, le=15)
    target_confidence: float = Field(default=0.9, gt=0, le=1)


@router.post("/ground-truth")
async def run_ground_truth(
    request: GroundTruthRequest, db: AsyncSession = Depends(get_db)
):
    from app.services.config_management import get_config_with_relations
    from app.services.iterative_ground_truth import run_ground_truth_loop

    try:
        config = await get_config_with_relations(request.config_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Config non trouvee")

    async def event_generator():
        try:
            async for item in run_ground_truth_loop(
                config=config,
                db=db,
                ticket_count=request.ticket_count,
                max_rounds=request.max_rounds,
                target_confidence=request.target_confidence,
            ):
                yield {
                    "event": item["type"],
                    "data": json.dumps(item.get("data", {}), ensure_ascii=False, default=str),
                }
        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Erreur interne : {exc}"}, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator(), ping=20)
