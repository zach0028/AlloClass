from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/api/import", tags=["Import"])


@router.post("/csv", response_model=MessageResponse, status_code=201)
async def import_csv(
    file: UploadFile,
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    from app.services.csv_import import import_tickets_from_csv

    try:
        result = await import_tickets_from_csv(file, config_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Config non trouvee")
    return MessageResponse(
        message=f"Import termine : {result['imported']} tickets importes, {result['skipped']} ignores, {result['errors']} erreurs"
    )
