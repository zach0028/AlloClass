from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import Config


async def execute_tool(
    tool_name: str,
    arguments: dict,
    config: Config,
    db: AsyncSession,
) -> dict:
    executors = {
        "classify_ticket": _classify_ticket,
        "classify_batch": _classify_batch,
        "search_tickets": _search_tickets,
        "correct_classification": _correct_classification,
        "get_review_queue": _get_review_queue,
        "get_stats": _get_stats,
        "get_improvement_suggestions": _get_improvement_suggestions,
        "get_config_info": _get_config_info,
        "get_learned_rules": _get_learned_rules,
        "get_version_history": _get_version_history,
    }

    executor = executors.get(tool_name)
    if not executor:
        return {"error": f"Outil inconnu : {tool_name}"}

    return await executor(arguments, config, db)


async def _classify_ticket(args: dict, config: Config, db: AsyncSession) -> dict:
    from app.services.classification_pipeline import classify_ticket

    classification = await classify_ticket(args["text"], config, db)
    return {
        "classification_id": str(classification.id),
        "input_text": args["text"][:100],
        "results": classification.results,
        "overall_confidence": classification.overall_confidence,
        "was_challenged": classification.was_challenged,
        "challenger_response": classification.challenger_response,
        "processing_time_ms": classification.processing_time_ms,
    }


async def _search_tickets(args: dict, config: Config, db: AsyncSession) -> dict:
    from app.services.ticket_query import (
        query_tickets_natural_language,
        query_tickets_semantic,
    )

    result = await query_tickets_natural_language(args["query"], config.id, db)
    if result.get("total_count", 0) == 0 and not result.get("results"):
        result = await query_tickets_semantic(args["query"], config.id, db)
    return result


async def _correct_classification(args: dict, config: Config, db: AsyncSession) -> dict:
    from app.services.feedback_learning import process_natural_feedback

    result = await process_natural_feedback(args["feedback_message"], config.id, db)
    return result


async def _get_review_queue(args: dict, config: Config, db: AsyncSession) -> dict:
    from app.services.feedback_learning import get_priority_queue

    count = args.get("count", 1)
    queue = await get_priority_queue(config.id, db, limit=count)
    if queue:
        return {"tickets": queue, "count": len(queue)}
    return {"tickets": [], "count": 0, "message": "Aucun ticket en attente de revision."}


async def _get_stats(args: dict, config: Config, db: AsyncSession) -> dict:
    from app.services.analytics_computation import compute_kpis

    return await compute_kpis(config.id, db)


async def _get_improvement_suggestions(args: dict, config: Config, db: AsyncSession) -> dict:
    from app.services.error_pattern_detector import generate_suggestions

    raw_suggestions = await generate_suggestions(config.id, db)
    return {"suggestions": raw_suggestions}


async def _get_config_info(args: dict, config: Config, db: AsyncSession) -> dict:
    axes_info = []
    for axis in sorted(config.axes, key=lambda a: a.position):
        categories = [
            {"name": cat.name, "description": cat.description}
            for cat in sorted(axis.categories, key=lambda c: c.position)
        ]
        axes_info.append({
            "name": axis.name,
            "description": axis.description,
            "categories": categories,
        })

    return {
        "config_name": config.name,
        "config_description": config.description,
        "axes_count": len(axes_info),
        "axes": axes_info,
    }


async def _classify_batch(args: dict, config: Config, db: AsyncSession) -> dict:
    from app.services.classification_pipeline import classify_batch

    texts = args["texts"]
    results = await classify_batch(texts, config, db)
    return {
        "count": len(results),
        "results": [
            {
                "classification_id": str(r.id),
                "input_text": r.input_text[:100],
                "results": r.results,
                "overall_confidence": r.overall_confidence,
            }
            for r in results
        ],
    }


async def _get_learned_rules(args: dict, config: Config, db: AsyncSession) -> dict:
    from sqlalchemy.orm import selectinload

    from app.models.learned_rule import LearnedRule

    result = await db.execute(
        select(LearnedRule)
        .options(selectinload(LearnedRule.axis))
        .where(
            LearnedRule.config_id == config.id,
            LearnedRule.active == True,
            LearnedRule.validated_by_user == True,
        )
        .order_by(LearnedRule.created_at)
    )
    rules = list(result.scalars().all())

    if not rules:
        return {"rules": [], "message": "Aucune regle apprise pour le moment."}
    return {
        "count": len(rules),
        "rules": [
            {
                "axis": r.axis.name if r.axis else "general",
                "rule_text": r.rule_text,
                "source_feedback_count": r.source_feedback_count,
                "validated_by_user": r.validated_by_user,
            }
            for r in rules
        ],
    }


async def _get_version_history(args: dict, config: Config, db: AsyncSession) -> dict:
    from app.services.prompt_versioning import get_version_history

    versions = await get_version_history(config.id, db)
    if not versions:
        return {"versions": [], "message": "Aucun historique de version."}
    return {
        "count": len(versions),
        "versions": [
            {
                "version": v.version_number,
                "created_at": str(v.created_at),
                "change_type": v.change_type,
                "change_description": v.change_description,
                "accuracy_at_creation": v.accuracy_at_creation,
            }
            for v in versions
        ],
    }
