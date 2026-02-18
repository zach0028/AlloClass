from uuid import UUID

import yaml
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import MessageResponse
from app.schemas.config import ConfigCreate, ConfigResponse, TemplateResponse
from app.services.config_management import (
    PRESETS_DIR,
    create_config as svc_create_config,
    delete_config as svc_delete_config,
    export_config_yaml as svc_export_yaml,
    get_config_with_relations,
    list_configs as svc_list_configs,
    update_config as svc_update_config,
)

router = APIRouter(prefix="/api/configs", tags=["Configs"])


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates():
    templates = []
    for path in sorted(PRESETS_DIR.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        axes = raw.get("axes", [])
        categories_count = sum(len(ax.get("categories", [])) for ax in axes)
        templates.append(
            TemplateResponse(
                name=raw["name"],
                description=raw.get("description", ""),
                axes_count=len(axes),
                categories_count=categories_count,
            )
        )
    return templates


@router.post("", response_model=ConfigResponse, status_code=201)
async def create_config(request: ConfigCreate, db: AsyncSession = Depends(get_db)):
    config = await svc_create_config(request.model_dump(), db)
    return config


@router.get("", response_model=list[ConfigResponse])
async def list_configs(db: AsyncSession = Depends(get_db)):
    return await svc_list_configs(db)


@router.get("/{config_id}", response_model=ConfigResponse)
async def get_config(config_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await get_config_with_relations(config_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Config non trouvee")


@router.put("/{config_id}", response_model=ConfigResponse)
async def update_config(
    config_id: UUID, request: ConfigCreate, db: AsyncSession = Depends(get_db)
):
    try:
        return await svc_update_config(config_id, request.model_dump(), db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Config non trouvee")


@router.delete("/{config_id}", response_model=MessageResponse)
async def delete_config(config_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        await svc_delete_config(config_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Config non trouvee")
    return MessageResponse(message="Config supprimee")


@router.get("/{config_id}/export")
async def export_config_yaml(config_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        yaml_str = await svc_export_yaml(config_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Config non trouvee")
    return Response(
        content=yaml_str,
        media_type="application/x-yaml",
        headers={"Content-Disposition": f"attachment; filename={config_id}.yaml"},
    )
