import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, func, or_, text, cast
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.messages import HumanMessage

from app.core.llm import classifier_llm
from app.models.classification_result import ClassificationResult
from app.models.user_feedback import UserFeedback
from app.prompts.ticket_query import TICKET_QUERY_PROMPT, TICKET_QUERY_SEMANTIC_PROMPT
from app.schemas.llm_outputs import TicketQueryOutput, SemanticQueryOutput
from app.services.shared.prompt_helpers import build_axes_text
from app.services.shared.vector_search import compute_embedding


async def query_tickets_natural_language(
    message: str, config_id: UUID, db: AsyncSession
) -> dict:
    from app.services.config.config_management import get_config_with_relations

    config = await get_config_with_relations(config_id, db)
    axes_text = build_axes_text(config)

    structured_llm = classifier_llm.with_structured_output(TicketQueryOutput)
    try:
        parsed = await structured_llm.ainvoke([
            HumanMessage(content=TICKET_QUERY_PROMPT.format(
                axes_and_categories=axes_text, message=message,
            )),
        ])
    except Exception:
        return {
            "interpretation": "Impossible de comprendre la requete.",
            "total_count": 0,
            "results": [],
        }

    filters = parsed.filters
    sort_by = parsed.sort
    limit = min(parsed.limit, 100)
    aggregation = parsed.aggregation

    query = select(ClassificationResult).where(
        ClassificationResult.config_id == config_id
    )

    query = _apply_date_filter(query, filters.date_range)
    query = _apply_confidence_filters(
        query, filters.confidence_min, filters.confidence_max
    )
    query = _apply_challenged_filter(query, filters.was_challenged)
    query = _apply_feedback_filter(query, filters.has_feedback)
    query = _apply_text_search(query, filters.text_search)
    query = _apply_axes_filters(query, filters.axes)

    if aggregation == "count":
        count_q = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_q)
        total = result.scalar() or 0
        return {
            "interpretation": f"{total} ticket(s) correspondent a votre recherche.",
            "total_count": total,
            "results": [],
        }

    query = _apply_sort(query, sort_by)
    query = query.limit(limit)

    result = await db.execute(query)
    rows = list(result.scalars().all())

    return {
        "interpretation": _build_interpretation(filters, len(rows)),
        "total_count": len(rows),
        "results": [_format_result(r) for r in rows],
    }


async def query_tickets_semantic(
    message: str, config_id: UUID, db: AsyncSession, limit: int = 20
) -> dict:
    structured_llm = classifier_llm.with_structured_output(SemanticQueryOutput)
    try:
        output = await structured_llm.ainvoke([
            HumanMessage(content=TICKET_QUERY_SEMANTIC_PROMPT.format(message=message)),
        ])
        search_text = output.search_text
        result_limit = min(output.limit, 100)
    except Exception:
        search_text = message
        result_limit = min(limit, 100)

    embedding = await compute_embedding(search_text)

    sql = text("""
        SELECT id, input_text, results, overall_confidence,
               was_challenged, challenger_response, created_at,
               embedding <=> :embedding AS distance
        FROM classification_results
        WHERE config_id = :config_id
          AND embedding IS NOT NULL
        ORDER BY embedding <=> :embedding
        LIMIT :limit
    """)

    result = await db.execute(
        sql,
        {"embedding": str(embedding), "config_id": str(config_id), "limit": result_limit},
    )
    rows = result.fetchall()

    return {
        "interpretation": f"Les {len(rows)} tickets les plus similaires a '{search_text}'.",
        "total_count": len(rows),
        "results": [
            {
                "id": str(row.id),
                "text_preview": row.input_text[:150] + ("..." if len(row.input_text) > 150 else ""),
                "classification": _simplify_results(row.results),
                "confidence": row.overall_confidence,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "similarity": round(1 - row.distance, 3),
            }
            for row in rows
        ],
    }


def _apply_date_filter(query, date_range):
    if not date_range or date_range == "all":
        return query

    now = datetime.now(timezone.utc)

    if date_range == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_range == "last_week":
        start = now - timedelta(days=7)
    elif date_range == "last_month":
        start = now - timedelta(days=30)
    elif ":" in date_range:
        parts = date_range.split(":")
        start = datetime.fromisoformat(parts[0])
        if len(parts) > 1:
            end = datetime.fromisoformat(parts[1])
            query = query.where(ClassificationResult.created_at <= end)
    else:
        return query

    return query.where(ClassificationResult.created_at >= start)


def _apply_confidence_filters(query, conf_min, conf_max):
    if conf_min is not None:
        query = query.where(ClassificationResult.overall_confidence >= conf_min)
    if conf_max is not None:
        query = query.where(ClassificationResult.overall_confidence <= conf_max)
    return query


def _apply_challenged_filter(query, was_challenged):
    if was_challenged is not None:
        query = query.where(ClassificationResult.was_challenged == was_challenged)
    return query


def _apply_feedback_filter(query, has_feedback):
    if has_feedback is None:
        return query
    fb_subquery = select(UserFeedback.classification_id).where(
        UserFeedback.active == True
    )
    if has_feedback:
        return query.where(ClassificationResult.id.in_(fb_subquery))
    return query.where(~ClassificationResult.id.in_(fb_subquery))


def _apply_text_search(query, text_search):
    if text_search:
        escaped = (
            text_search
            .replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        query = query.where(
            ClassificationResult.input_text.ilike(f"%{escaped}%")
        )
    return query


def _apply_axes_filters(query, axes_filters):
    for axis_filter in axes_filters:
        axis_name = axis_filter.axis_name if hasattr(axis_filter, "axis_name") else axis_filter.get("axis_name", "")
        categories = axis_filter.categories if hasattr(axis_filter, "categories") else axis_filter.get("categories", [])
        if not categories:
            continue
        cat_conditions = []
        for cat in categories:
            target = json.dumps([{"axis_name": axis_name, "category_name": cat}])
            cat_conditions.append(
                ClassificationResult.results.op("@>")(cast(target, JSONB))
            )
        query = query.where(or_(*cat_conditions))
    return query


def _apply_sort(query, sort_by):
    sort_map = {
        "created_at_desc": ClassificationResult.created_at.desc(),
        "created_at_asc": ClassificationResult.created_at.asc(),
        "confidence_desc": ClassificationResult.overall_confidence.desc(),
        "confidence_asc": ClassificationResult.overall_confidence.asc(),
    }
    return query.order_by(sort_map.get(sort_by, ClassificationResult.created_at.desc()))


def _format_result(classification: ClassificationResult) -> dict:
    return {
        "id": str(classification.id),
        "text_preview": classification.input_text[:150] + (
            "..." if len(classification.input_text) > 150 else ""
        ),
        "classification": _simplify_results(classification.results),
        "confidence": classification.overall_confidence,
        "was_challenged": classification.was_challenged,
        "created_at": classification.created_at.isoformat() if classification.created_at else None,
    }


def _simplify_results(results: list[dict] | None) -> dict:
    if not results:
        return {}
    return {r["axis_name"]: r["category_name"] for r in results if "axis_name" in r}


def _build_interpretation(filters, count: int) -> str:
    parts = []
    for axis_filter in filters.axes:
        name = axis_filter.axis_name if hasattr(axis_filter, "axis_name") else axis_filter.get("axis_name", "")
        cats = axis_filter.categories if hasattr(axis_filter, "categories") else axis_filter.get("categories", [])
        if cats:
            parts.append(f"{name} = {', '.join(cats)}")

    date_range = filters.date_range if hasattr(filters, "date_range") else filters.get("date_range")
    if date_range and date_range != "all":
        date_labels = {
            "today": "aujourd'hui",
            "last_week": "7 derniers jours",
            "last_month": "30 derniers jours",
        }
        parts.append(date_labels.get(date_range, date_range))

    conf_min = filters.confidence_min if hasattr(filters, "confidence_min") else filters.get("confidence_min")
    if conf_min is not None:
        parts.append(f"confiance >= {int(conf_min * 100)}%")

    interpretation = " | ".join(parts) if parts else "Tous les tickets"
    return f"{interpretation} — {count} resultat(s)"
