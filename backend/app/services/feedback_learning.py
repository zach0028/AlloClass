import json
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.openai_client import client as openai_client
from app.models.axis import Axis
from app.models.axis_category import AxisCategory
from app.models.classification_result import ClassificationResult
from app.models.user_feedback import UserFeedback
from app.prompts.feedback_parser import FEEDBACK_PARSER_SYSTEM_PROMPT
from app.services.prompt_helpers import build_axes_text


async def store_feedback(
    classification_id: UUID,
    axis_id: UUID,
    corrected_category_id: UUID | None,
    reasoning_feedback: str | None,
    feedback_type: str,
    db: AsyncSession,
) -> UserFeedback:
    review_status = "non_reviewed"
    original_category_id = None

    if corrected_category_id is not None:
        classification = await db.get(ClassificationResult, classification_id)
        if classification and classification.results:
            for r in classification.results:
                if r.get("axis_id") == str(axis_id):
                    original_category_id = r.get("category_id")
                    break

            if original_category_id is not None:
                if str(corrected_category_id) == original_category_id:
                    review_status = "validated"
                else:
                    review_status = "corrected"
            else:
                review_status = "corrected"

    original_cat_uuid = UUID(original_category_id) if original_category_id else None

    feedback = UserFeedback(
        classification_id=classification_id,
        axis_id=axis_id,
        corrected_category_id=corrected_category_id,
        original_category_id=original_cat_uuid,
        reasoning_feedback=reasoning_feedback,
        feedback_type=feedback_type,
        review_status=review_status,
        active=True,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return feedback


async def process_natural_feedback(
    message: str, config_id: UUID, db: AsyncSession
) -> dict:
    last_classification = await db.execute(
        select(ClassificationResult)
        .where(ClassificationResult.config_id == config_id)
        .order_by(ClassificationResult.created_at.desc())
        .limit(1)
    )
    classification = last_classification.scalar_one_or_none()

    if classification is None:
        return {"success": False, "message": "Aucune classification recente trouvee."}

    from app.services.config_management import get_config_with_relations
    config = await get_config_with_relations(config_id, db)
    axes_text = build_axes_text(config)

    current_results = json.dumps(classification.results, ensure_ascii=False, indent=2)

    system_prompt = FEEDBACK_PARSER_SYSTEM_PROMPT.format(
        axes_and_categories=axes_text,
        current_results=current_results,
    )

    response = await openai_client.chat.completions.create(
        model=settings.classifier_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        reasoning_effort="low",
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return {"success": False, "message": "Impossible de comprendre le feedback."}

    axis_name = parsed.get("axis_name", "")
    corrected_cat_name = parsed.get("corrected_category", "")

    target_axis = next((a for a in config.axes if a.name == axis_name), None)
    if target_axis is None:
        return {"success": False, "message": f"Axe '{axis_name}' non reconnu."}

    target_cat = next(
        (c for c in target_axis.categories if c.name == corrected_cat_name), None
    )
    if target_cat is None:
        return {
            "success": False,
            "message": f"Categorie '{corrected_cat_name}' non trouvee sur l'axe '{axis_name}'.",
        }

    feedback = await store_feedback(
        classification_id=classification.id,
        axis_id=target_axis.id,
        corrected_category_id=target_cat.id,
        reasoning_feedback=parsed.get("reasoning"),
        feedback_type="corrected",
        db=db,
    )

    from app.services.learning_explainer import explain_learning
    learning_card = await explain_learning(feedback.id, db)

    return {
        "success": True,
        "message": f"Correction enregistree : axe '{axis_name}' → '{corrected_cat_name}'.",
        "feedback_id": str(feedback.id),
        "learning_card": learning_card,
    }


def _compute_priority_score(
    classification: ClassificationResult,
    is_early: bool,
    cat_fb_counts: dict[tuple[str, str], int],
) -> float:
    confidence_score = 1.0 - classification.overall_confidence

    challenged_score = 1.0 if classification.was_challenged else 0.0

    disagreement_score = 0.0
    if classification.vote_details and "results_per_axis" in classification.vote_details:
        non_unanimous = sum(
            1 for r in classification.vote_details["results_per_axis"]
            if r.get("empirical_confidence", 1.0) < 1.0
        )
        total_axes = len(classification.vote_details["results_per_axis"])
        if total_axes > 0:
            disagreement_score = non_unanimous / total_axes

    rarity_score = 0.0
    if classification.results:
        rarity_scores = []
        for r in classification.results:
            key = (r.get("axis_name", ""), r.get("category_name", ""))
            count = cat_fb_counts.get(key, 0)
            rarity_scores.append(1.0 / (1.0 + count))
        if rarity_scores:
            rarity_score = sum(rarity_scores) / len(rarity_scores)

    diversity_score = 0.5

    if is_early:
        score = (
            rarity_score * 0.35
            + confidence_score * 0.25
            + challenged_score * 0.20
            + disagreement_score * 0.15
            + diversity_score * 0.05
        )
    else:
        score = (
            disagreement_score * 0.30
            + confidence_score * 0.25
            + rarity_score * 0.20
            + challenged_score * 0.15
            + diversity_score * 0.10
        )

    return round(min(1.0, max(0.0, score)), 3)


async def get_priority_queue(
    config_id: UUID, db: AsyncSession, limit: int = 10
) -> list[dict]:
    pending_query = (
        select(ClassificationResult)
        .outerjoin(UserFeedback, UserFeedback.classification_id == ClassificationResult.id)
        .where(
            and_(
                ClassificationResult.config_id == config_id,
                UserFeedback.id.is_(None),
            )
        )
        .order_by(ClassificationResult.overall_confidence.asc())
        .limit(limit * 3)
    )
    result = await db.execute(pending_query)
    candidates = list(result.scalars().unique().all())

    if not candidates:
        return []

    total_fb_result = await db.execute(
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
    fb_count = total_fb_result.scalar() or 0
    is_early = fb_count < 30

    cat_counts_result = await db.execute(
        select(
            Axis.name.label("axis_name"),
            AxisCategory.name.label("cat_name"),
            func.count().label("cnt"),
        )
        .select_from(UserFeedback)
        .join(AxisCategory, UserFeedback.corrected_category_id == AxisCategory.id)
        .join(Axis, UserFeedback.axis_id == Axis.id)
        .where(UserFeedback.active == True)
        .group_by(Axis.name, AxisCategory.name)
    )
    cat_fb_counts = {
        (r.axis_name, r.cat_name): r.cnt
        for r in cat_counts_result.fetchall()
    }

    scored = []
    for c in candidates:
        score = _compute_priority_score(c, is_early, cat_fb_counts)

        reasons = []
        if c.overall_confidence < 0.75:
            reasons.append(f"Confiance faible ({int(c.overall_confidence * 100)}%)")
        if c.was_challenged:
            reasons.append("Challenger active")

        scored.append({
            "classification_id": str(c.id),
            "text_preview": c.input_text[:120] + ("..." if len(c.input_text) > 120 else ""),
            "priority_score": score,
            "reason": " + ".join(reasons) if reasons else "Score composite eleve",
            "current_classification": c.results,
            "challenger_opinion": c.challenger_response,
        })

    scored.sort(key=lambda x: x["priority_score"], reverse=True)
    return scored[:limit]
