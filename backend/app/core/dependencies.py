from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.config import Config


async def get_valid_config(
    config_id: UUID, db: AsyncSession = Depends(get_db)
) -> Config:
    config = await db.get(Config, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config
