from pathlib import Path
from uuid import UUID

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.axis import Axis
from app.models.axis_category import AxisCategory
from app.models.config import Config

PRESETS_DIR = Path(__file__).resolve().parent.parent / "presets"


async def ensure_default_config(db: AsyncSession) -> Config:
    result = await db.execute(
        select(Config)
        .options(selectinload(Config.axes).selectinload(Axis.categories))
        .limit(1)
    )
    config = result.scalar_one_or_none()
    if config is not None:
        return config

    return await load_preset("support-client", db)


async def load_preset(preset_name: str, db: AsyncSession) -> Config:
    preset_path = PRESETS_DIR / f"{preset_name}.yaml"
    if not preset_path.exists():
        raise FileNotFoundError(f"Preset '{preset_name}' not found at {preset_path}")

    raw = yaml.safe_load(preset_path.read_text(encoding="utf-8"))

    config = Config(
        name=raw["name"],
        description=raw.get("description", ""),
        template_source=raw.get("domain", preset_name),
    )
    db.add(config)
    await db.flush()

    for ax_pos, ax_data in enumerate(raw["axes"]):
        axis = Axis(
            config_id=config.id,
            name=ax_data["name"],
            description=ax_data.get("description", ""),
            position=ax_pos,
        )
        db.add(axis)
        await db.flush()

        for cat_pos, cat_data in enumerate(ax_data.get("categories", [])):
            category = AxisCategory(
                axis_id=axis.id,
                name=cat_data["name"],
                description=cat_data.get("description", ""),
                position=cat_pos,
            )
            db.add(category)

    await db.commit()
    return await get_config_with_relations(config.id, db)


async def get_config_with_relations(config_id: UUID, db: AsyncSession) -> Config:
    result = await db.execute(
        select(Config)
        .where(Config.id == config_id)
        .options(selectinload(Config.axes).selectinload(Axis.categories))
    )
    config = result.scalar_one_or_none()
    if config is None:
        raise ValueError(f"Config {config_id} not found")
    return config


async def list_configs(db: AsyncSession) -> list[Config]:
    result = await db.execute(
        select(Config)
        .options(selectinload(Config.axes).selectinload(Axis.categories))
        .order_by(Config.created_at.desc())
    )
    return list(result.scalars().all())


async def export_config_yaml(config_id: UUID, db: AsyncSession) -> str:
    config = await get_config_with_relations(config_id, db)

    data = {
        "name": config.name,
        "description": config.description,
        "domain": config.template_source,
        "axes": [
            {
                "name": axis.name,
                "description": axis.description,
                "categories": [
                    {"name": cat.name, "description": cat.description}
                    for cat in sorted(axis.categories, key=lambda c: c.position)
                ],
            }
            for axis in sorted(config.axes, key=lambda a: a.position)
        ],
    }
    return yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)


async def create_config(data: dict, db: AsyncSession) -> Config:
    config = Config(
        name=data["name"],
        description=data.get("description", ""),
        template_source=data.get("template_source"),
    )
    db.add(config)
    await db.flush()

    for ax_pos, ax_data in enumerate(data.get("axes", [])):
        axis = Axis(
            config_id=config.id,
            name=ax_data["name"],
            description=ax_data.get("description", ""),
            position=ax_pos,
        )
        db.add(axis)
        await db.flush()

        for cat_pos, cat_data in enumerate(ax_data.get("categories", [])):
            category = AxisCategory(
                axis_id=axis.id,
                name=cat_data["name"],
                description=cat_data.get("description", ""),
                position=cat_pos,
            )
            db.add(category)

    await db.commit()
    return await get_config_with_relations(config.id, db)


async def update_config(config_id: UUID, data: dict, db: AsyncSession) -> Config:
    config = await get_config_with_relations(config_id, db)

    config.name = data.get("name", config.name)
    config.description = data.get("description", config.description)

    if "axes" in data:
        for axis in list(config.axes):
            await db.delete(axis)
        await db.flush()

        for ax_pos, ax_data in enumerate(data["axes"]):
            axis = Axis(
                config_id=config.id,
                name=ax_data["name"],
                description=ax_data.get("description", ""),
                position=ax_pos,
            )
            db.add(axis)
            await db.flush()

            for cat_pos, cat_data in enumerate(ax_data.get("categories", [])):
                category = AxisCategory(
                    axis_id=axis.id,
                    name=cat_data["name"],
                    description=cat_data.get("description", ""),
                    position=cat_pos,
                )
                db.add(category)

    await db.commit()
    return await get_config_with_relations(config.id, db)


async def delete_config(config_id: UUID, db: AsyncSession) -> None:
    config = await db.get(Config, config_id)
    if config is None:
        raise ValueError(f"Config {config_id} not found")
    await db.delete(config)
    await db.commit()
