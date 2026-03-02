from uuid import UUID

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.axis import Axis
from app.models.config import Config
from app.models.learned_rule import LearnedRule
from app.models.prompt_version import PromptVersion
from app.services.prompt_helpers import build_axes_text


async def create_version(
    config_id: UUID,
    change_type: str,
    change_description: str,
    db: AsyncSession,
) -> PromptVersion:
    max_stmt = (
        select(sa_func.coalesce(sa_func.max(PromptVersion.version_number), 0))
        .where(PromptVersion.config_id == config_id)
    )
    current_max = (await db.execute(max_stmt)).scalar()
    next_version = current_max + 1

    config_stmt = (
        select(Config)
        .where(Config.id == config_id)
    )
    config = (await db.execute(config_stmt)).scalar_one()

    axes_stmt = (
        select(Axis)
        .where(Axis.config_id == config_id)
        .order_by(Axis.position)
    )
    axes = (await db.execute(axes_stmt)).scalars().all()
    config.axes = list(axes)

    prompt_snapshot = {
        "axes_text": build_axes_text(config),
    }

    rules_stmt = (
        select(LearnedRule)
        .where(
            LearnedRule.config_id == config_id,
            LearnedRule.active.is_(True),
        )
    )
    active_rules = (await db.execute(rules_stmt)).scalars().all()
    learned_rules_snapshot = [
        {
            "id": str(r.id),
            "rule_text": r.rule_text,
            "axis_id": str(r.axis_id) if r.axis_id else None,
            "source_feedback_count": r.source_feedback_count,
        }
        for r in active_rules
    ]

    thresholds_snapshot = {
        a.name: a.challenger_threshold for a in axes
    }

    version = PromptVersion(
        config_id=config_id,
        version_number=next_version,
        change_type=change_type,
        change_description=change_description,
        prompt_snapshot=prompt_snapshot,
        learned_rules_snapshot=learned_rules_snapshot,
        challenger_thresholds_snapshot=thresholds_snapshot,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version


async def get_version_history(
    config_id: UUID, db: AsyncSession
) -> list[PromptVersion]:
    stmt = (
        select(PromptVersion)
        .where(PromptVersion.config_id == config_id)
        .order_by(PromptVersion.version_number.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


