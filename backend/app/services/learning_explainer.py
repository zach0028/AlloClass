from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.axis import Axis
from app.models.axis_category import AxisCategory
from app.models.classification_result import ClassificationResult
from app.models.learned_rule import LearnedRule
from app.models.user_feedback import UserFeedback


async def explain_learning(
    feedback_id: UUID, db: AsyncSession
) -> dict:
    feedback = await db.get(UserFeedback, feedback_id)
    if feedback is None:
        return {"level_1": {"active": False, "message": "Feedback introuvable."}}

    classification = await db.get(ClassificationResult, feedback.classification_id)
    axis = await db.get(Axis, feedback.axis_id)
    corrected_cat = None
    if feedback.corrected_category_id:
        corrected_cat = await db.get(AxisCategory, feedback.corrected_category_id)

    config_id = classification.config_id if classification else None

    axis_name = axis.name if axis else "inconnu"
    cat_name = corrected_cat.name if corrected_cat else "inchangee"

    level_1 = {
        "active": True,
        "message": (
            f"Je retiens cette correction sur l'axe '{axis_name}' → '{cat_name}'. "
            f"Les prochains tickets similaires seront mieux classes grace a cet exemple."
        ),
    }

    level_2 = {"active": False, "message": "", "proposed_rule": None}
    if config_id and feedback.axis_id:
        from app.services.error_pattern_detector import detect_rule_candidates

        candidates = await detect_rule_candidates(config_id, db)
        axis_candidates = [
            c for c in candidates if c.get("axis_id") == str(feedback.axis_id)
        ]
        if axis_candidates:
            best = max(axis_candidates, key=lambda c: c["source_feedback_count"])
            level_2 = {
                "active": True,
                "message": (
                    f"J'ai detecte un pattern recurrent ({best['source_feedback_count']} corrections) : "
                    f"'{best['proposed_rule_text']}'. Veux-tu que j'en fasse une regle permanente ?"
                ),
                "proposed_rule": best,
            }

    level_3 = {"active": False, "message": "", "calibration_warning": None}
    if config_id:
        from app.services.self_consistency_voting import compute_axis_disagreement

        disagreements = await compute_axis_disagreement(config_id, db)
        high_disagreement = [d for d in disagreements if d["disagreement_rate"] > 0.25]

        if high_disagreement:
            worst = max(high_disagreement, key=lambda d: d["disagreement_rate"])
            rate_pct = int(worst["disagreement_rate"] * 100)
            level_3["active"] = True
            level_3["message"] = (
                f"L'axe '{worst['axis_name']}' a un taux de desaccord de {rate_pct}%. "
                f"Je propose de passer le seuil Challenger de 0.75 a {worst['suggested_threshold']} "
                f"pour challenger plus souvent sur cet axe."
            )

        total_feedbacks = await db.execute(
            select(func.count())
            .select_from(UserFeedback)
            .join(ClassificationResult, UserFeedback.classification_id == ClassificationResult.id)
            .where(
                and_(
                    ClassificationResult.config_id == config_id,
                    UserFeedback.active == True,
                    UserFeedback.review_status.in_(["corrected", "validated"]),
                )
            )
        )
        fb_count = total_feedbacks.scalar() or 0

        if fb_count >= 20:
            corrected_count = await db.execute(
                select(func.count())
                .select_from(UserFeedback)
                .join(ClassificationResult, UserFeedback.classification_id == ClassificationResult.id)
                .where(
                    and_(
                        ClassificationResult.config_id == config_id,
                        UserFeedback.active == True,
                        UserFeedback.review_status == "corrected",
                    )
                )
            )
            corr_count = corrected_count.scalar() or 0
            error_rate = round(corr_count / fb_count, 2) if fb_count > 0 else 0

            if error_rate > 0.3:
                level_3["calibration_warning"] = (
                    f"Le systeme est corrige {int(error_rate * 100)}% du temps. "
                    f"Les scores de confiance affiches sont probablement trop optimistes."
                )

    return {
        "level_1": level_1,
        "level_2": level_2,
        "level_3": level_3,
    }


async def get_active_learned_rules(
    config_id: UUID, db: AsyncSession
) -> list[LearnedRule]:
    result = await db.execute(
        select(LearnedRule)
        .where(
            and_(
                LearnedRule.config_id == config_id,
                LearnedRule.active == True,
                LearnedRule.validated_by_user == True,
            )
        )
        .order_by(LearnedRule.created_at)
    )
    return list(result.scalars().all())
