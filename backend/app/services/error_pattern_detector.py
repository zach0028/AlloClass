import json
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.openai_client import client as openai_client
from app.models.axis import Axis
from app.models.axis_category import AxisCategory
from app.models.classification_result import ClassificationResult
from app.models.learned_rule import LearnedRule
from app.models.user_feedback import UserFeedback
from app.prompts.error_patterns import ERROR_PATTERN_PROMPT
from app.services.prompt_helpers import build_axes_text


async def detect_error_patterns(
    config_id: UUID, db: AsyncSession
) -> list[dict]:
    from app.services.config_management import get_config_with_relations
    config = await get_config_with_relations(config_id, db)

    query = (
        select(
            UserFeedback.axis_id,
            Axis.name.label("axis_name"),
            ClassificationResult.input_text,
            ClassificationResult.results,
            AxisCategory.name.label("corrected_category_name"),
            UserFeedback.reasoning_feedback,
        )
        .join(ClassificationResult, UserFeedback.classification_id == ClassificationResult.id)
        .join(Axis, UserFeedback.axis_id == Axis.id)
        .join(AxisCategory, UserFeedback.corrected_category_id == AxisCategory.id)
        .where(
            and_(
                ClassificationResult.config_id == config_id,
                UserFeedback.active == True,
                UserFeedback.review_status == "corrected",
            )
        )
        .order_by(UserFeedback.created_at.desc())
        .limit(50)
    )
    result = await db.execute(query)
    rows = result.fetchall()

    if len(rows) < 3:
        return []

    feedbacks_summary = "\n".join(
        f"- Ticket: \"{row.input_text[:100]}...\" | Axe: {row.axis_name} | "
        f"Corrige vers: {row.corrected_category_name} | Raison: {row.reasoning_feedback or 'N/A'}"
        for row in rows
    )

    axes_text = build_axes_text(config)

    response = await openai_client.chat.completions.create(
        model=settings.challenger_model,
        messages=[
            {
                "role": "user",
                "content": ERROR_PATTERN_PROMPT.format(
                    feedbacks_summary=feedbacks_summary,
                    axes_and_categories=axes_text,
                ),
            }
        ],
        reasoning_effort="medium",
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            parsed = parsed.get("patterns", parsed.get("results", []))
        if not isinstance(parsed, list):
            parsed = []
    except (json.JSONDecodeError, TypeError):
        parsed = []

    axis_map = {a.name: str(a.id) for a in config.axes}
    for pattern in parsed:
        axis_name = pattern.get("axis_name", "")
        pattern["axis_id"] = axis_map.get(axis_name)

    return parsed


async def detect_rule_candidates(
    config_id: UUID, db: AsyncSession
) -> list[dict]:
    ac_original = AxisCategory.__table__.alias("ac_original")
    ac_corrected = AxisCategory.__table__.alias("ac_corrected")

    query = (
        select(
            UserFeedback.axis_id,
            Axis.name.label("axis_name"),
            ac_original.c.name.label("original_category_name"),
            ac_corrected.c.name.label("corrected_category_name"),
            func.count().label("correction_count"),
        )
        .join(ClassificationResult, UserFeedback.classification_id == ClassificationResult.id)
        .join(Axis, UserFeedback.axis_id == Axis.id)
        .join(ac_corrected, UserFeedback.corrected_category_id == ac_corrected.c.id)
        .join(ac_original, UserFeedback.original_category_id == ac_original.c.id)
        .where(
            and_(
                ClassificationResult.config_id == config_id,
                UserFeedback.active == True,
                UserFeedback.review_status == "corrected",
                UserFeedback.corrected_category_id.isnot(None),
                UserFeedback.original_category_id.isnot(None),
            )
        )
        .group_by(
            UserFeedback.axis_id, Axis.name,
            ac_original.c.name, ac_corrected.c.name,
        )
        .having(func.count() >= 1)
    )
    result = await db.execute(query)
    rows = result.fetchall()

    if not rows:
        return []

    existing_rules = await db.execute(
        select(LearnedRule.rule_text).where(
            and_(
                LearnedRule.config_id == config_id,
                LearnedRule.active == True,
            )
        )
    )
    active_rule_texts = {r.rule_text for r in existing_rules.fetchall()}

    candidates = []
    for row in rows:
        proposed_text = (
            f"Sur l'axe '{row.axis_name}', quand le classifieur propose "
            f"'{row.original_category_name}', corriger vers "
            f"'{row.corrected_category_name}' "
            f"(base sur {row.correction_count} corrections)."
        )

        if proposed_text in active_rule_texts:
            continue

        candidates.append({
            "axis_id": str(row.axis_id),
            "axis_name": row.axis_name,
            "from_category": row.original_category_name,
            "to_category": row.corrected_category_name,
            "source_feedback_count": row.correction_count,
            "proposed_rule_text": proposed_text,
        })

    return candidates


async def generate_suggestions(
    config_id: UUID, db: AsyncSession
) -> list[dict]:
    total_feedbacks = await db.execute(
        select(func.count())
        .select_from(UserFeedback)
        .join(ClassificationResult, UserFeedback.classification_id == ClassificationResult.id)
        .where(
            and_(
                ClassificationResult.config_id == config_id,
                UserFeedback.active == True,
            )
        )
    )
    feedback_count = total_feedbacks.scalar() or 0

    suggestions = []

    if feedback_count < 20:
        suggestions.append({
            "type": "insufficient_data",
            "message": f"Seulement {feedback_count} feedbacks. "
                       f"Minimum 20 recommandes pour des suggestions fiables.",
            "axis_id": None,
            "details": {"current": feedback_count, "minimum": 20},
        })
        return suggestions

    patterns = await detect_error_patterns(config_id, db)
    for p in patterns:
        suggestions.append({
            "type": p.get("pattern_type", "pattern"),
            "message": p.get("proposed_rule", p.get("trigger_description", "")),
            "axis_id": p.get("axis_id"),
            "details": p,
        })

    from app.services.config_management import get_config_with_relations
    config = await get_config_with_relations(config_id, db)

    for axis in config.axes:
        axis_feedback_count = await db.execute(
            select(func.count())
            .select_from(UserFeedback)
            .where(
                and_(
                    UserFeedback.axis_id == axis.id,
                    UserFeedback.active == True,
                )
            )
        )
        count = axis_feedback_count.scalar() or 0
        if count == 0:
            suggestions.append({
                "type": "no_feedback_axis",
                "message": f"L'axe '{axis.name}' n'a encore aucun feedback. "
                           f"Les corrections sur cet axe seraient tres utiles.",
                "axis_id": str(axis.id),
                "details": {"axis_name": axis.name},
            })

    return suggestions
