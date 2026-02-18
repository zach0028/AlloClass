from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.classification import (
    ClassificationResponse,
    ClassifyBatchRequest,
    ClassifyRequest,
)
from app.services.classification_pipeline import (
    classify_batch as svc_classify_batch,
    classify_ticket,
)
from app.services.config_management import get_config_with_relations

router = APIRouter(prefix="/api/classify", tags=["Classification"])


@router.post("", response_model=ClassificationResponse, status_code=201)
async def classify(request: ClassifyRequest, db: AsyncSession = Depends(get_db)):
    try:
        config = await get_config_with_relations(request.config_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Config non trouvee")
    result = await classify_ticket(request.text, config, db)
    return result


@router.post("/batch", response_model=list[ClassificationResponse], status_code=201)
async def classify_batch(
    request: ClassifyBatchRequest, db: AsyncSession = Depends(get_db)
):
    try:
        config = await get_config_with_relations(request.config_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Config non trouvee")
    results = await svc_classify_batch(request.texts, config, db)
    return results
