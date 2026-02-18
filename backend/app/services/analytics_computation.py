from collections import defaultdict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classification_result import ClassificationResult
from app.models.user_feedback import UserFeedback


async def compute_kpis(config_id: UUID, db: AsyncSession) -> dict:
    total_stmt = (
        select(func.count())
        .select_from(ClassificationResult)
        .where(ClassificationResult.config_id == config_id)
    )
    total = (await db.execute(total_stmt)).scalar() or 0

    avg_stmt = (
        select(func.avg(ClassificationResult.overall_confidence))
        .where(ClassificationResult.config_id == config_id)
    )
    avg_confidence = (await db.execute(avg_stmt)).scalar()

    challenged_stmt = (
        select(func.count())
        .select_from(ClassificationResult)
        .where(
            ClassificationResult.config_id == config_id,
            ClassificationResult.was_challenged.is_(True),
        )
    )
    challenged = (await db.execute(challenged_stmt)).scalar() or 0

    feedback_stmt = (
        select(func.count())
        .select_from(UserFeedback)
        .where(UserFeedback.classification_id.in_(
            select(ClassificationResult.id)
            .where(ClassificationResult.config_id == config_id)
        ))
    )
    feedback_count = (await db.execute(feedback_stmt)).scalar() or 0

    return {
        "total_classifications": total,
        "average_confidence": round(avg_confidence, 3) if avg_confidence else 0,
        "challenge_rate": round(challenged / total, 3) if total > 0 else 0,
        "feedback_count": feedback_count,
    }


async def compute_confidence_distribution(
    config_id: UUID, db: AsyncSession
) -> list[dict]:
    stmt = (
        select(ClassificationResult.overall_confidence)
        .where(ClassificationResult.config_id == config_id)
    )
    rows = (await db.execute(stmt)).scalars().all()

    buckets = [0] * 10
    for conf in rows:
        idx = min(int(conf * 10), 9)
        buckets[idx] += 1

    return [
        {
            "range": f"{i*10}-{(i+1)*10}%",
            "count": buckets[i],
        }
        for i in range(10)
    ]


async def compute_axes_stats(config_id: UUID, db: AsyncSession) -> list[dict]:
    classif_stmt = (
        select(
            ClassificationResult.id,
            ClassificationResult.results,
        )
        .where(ClassificationResult.config_id == config_id)
    )
    classif_rows = (await db.execute(classif_stmt)).all()

    fb_stmt = (
        select(
            UserFeedback.classification_id,
            UserFeedback.axis_id,
            UserFeedback.feedback_type,
        )
        .where(UserFeedback.classification_id.in_(
            select(ClassificationResult.id)
            .where(ClassificationResult.config_id == config_id)
        ))
    )
    fb_rows = (await db.execute(fb_stmt)).all()

    fb_by_classif: dict[UUID, dict[UUID, str]] = defaultdict(dict)
    for fb in fb_rows:
        fb_by_classif[fb.classification_id][fb.axis_id] = fb.feedback_type

    axis_stats: dict[str, dict] = {}

    for row in classif_rows:
        results_list = row.results if isinstance(row.results, list) else (row.results or {}).get("results", [])
        fbs = fb_by_classif.get(row.id, {})

        for r in results_list:
            axis_name = r.get("axis_name", "")
            cat_name = r.get("category_name", "")

            if axis_name not in axis_stats:
                axis_stats[axis_name] = {
                    "total": 0,
                    "correct": 0,
                    "with_feedback": 0,
                    "categories": defaultdict(int),
                }
            axis_stats[axis_name]["categories"][cat_name] += 1
            axis_stats[axis_name]["total"] += 1

            axis_id_str = r.get("axis_id")
            if axis_id_str:
                try:
                    axis_uuid = UUID(axis_id_str) if isinstance(axis_id_str, str) else axis_id_str
                except (ValueError, AttributeError):
                    continue
                fb_type = fbs.get(axis_uuid)
                if fb_type is not None:
                    axis_stats[axis_name]["with_feedback"] += 1
                    if fb_type == "validated":
                        axis_stats[axis_name]["correct"] += 1

    result = []
    for axis_name, stats in axis_stats.items():
        correct = stats["correct"]
        with_feedback = stats["with_feedback"]
        accuracy = round(correct / with_feedback, 3) if with_feedback > 0 else None

        cats = stats["categories"]
        top_categories = sorted(cats.items(), key=lambda x: -x[1])[:5]

        result.append({
            "axis_name": axis_name,
            "accuracy": accuracy,
            "total_classifications": stats["total"],
            "feedback_count": with_feedback,
            "top_categories": [
                {"name": name, "count": count} for name, count in top_categories
            ],
        })

    return result


async def compute_classification_matrix(
    config_id: UUID,
    db: AsyncSession,
    x_axis_name: str | None = None,
    y_axis_name: str | None = None,
) -> dict:
    from app.models.axis import Axis
    from app.models.axis_category import AxisCategory

    config_axes_stmt = (
        select(Axis.name, AxisCategory.name, AxisCategory.position)
        .join(AxisCategory, AxisCategory.axis_id == Axis.id)
        .where(Axis.config_id == config_id)
        .order_by(Axis.position, AxisCategory.position)
    )
    config_rows = (await db.execute(config_axes_stmt)).all()

    ordered_axes: dict[str, list[str]] = {}
    for axis_name, cat_name, _ in config_rows:
        ordered_axes.setdefault(axis_name, []).append(cat_name)

    stmt = select(
        ClassificationResult.results,
        ClassificationResult.overall_confidence,
    ).where(ClassificationResult.config_id == config_id)
    rows = (await db.execute(stmt)).all()

    if not rows:
        return {"axes": [], "x_axis": "", "y_axis": "", "cells": [], "total": 0}

    ticket_data: list[dict[str, str | float]] = []
    for row in rows:
        results_list = row.results if isinstance(row.results, list) else (row.results or {}).get("results", [])
        entry: dict[str, str | float] = {"confidence": row.overall_confidence}
        for r in results_list:
            axis_name = r.get("axis_name", "")
            cat_name = r.get("category_name", "")
            if axis_name:
                entry[axis_name] = cat_name
        ticket_data.append(entry)

    axis_names = list(ordered_axes.keys())
    if len(axis_names) < 2:
        return {
            "axes": [{"name": n, "categories": ordered_axes[n]} for n in axis_names],
            "x_axis": axis_names[0] if axis_names else "",
            "y_axis": "",
            "cells": [],
            "total": len(rows),
        }

    x_axis = x_axis_name if x_axis_name in ordered_axes else axis_names[0]
    y_axis = y_axis_name if y_axis_name in ordered_axes else axis_names[1]

    cell_counts: dict[tuple[str, str], list[float]] = defaultdict(list)
    for entry in ticket_data:
        x_cat = entry.get(x_axis)
        y_cat = entry.get(y_axis)
        if isinstance(x_cat, str) and isinstance(y_cat, str):
            cell_counts[(x_cat, y_cat)].append(float(entry["confidence"]))

    cells = [
        {
            "x_category": x_cat,
            "y_category": y_cat,
            "count": len(confidences),
            "avg_confidence": round(sum(confidences) / len(confidences), 3),
        }
        for (x_cat, y_cat), confidences in cell_counts.items()
    ]

    return {
        "axes": [{"name": n, "categories": ordered_axes[n]} for n in axis_names],
        "x_axis": x_axis,
        "y_axis": y_axis,
        "cells": cells,
        "total": len(rows),
    }


async def compute_embedding_map(config_id: UUID, db: AsyncSession) -> list[dict]:
    stmt = (
        select(
            ClassificationResult.id,
            ClassificationResult.embedding,
            ClassificationResult.results,
            ClassificationResult.overall_confidence,
            ClassificationResult.input_text,
        )
        .where(
            ClassificationResult.config_id == config_id,
            ClassificationResult.embedding.isnot(None),
        )
    )
    rows = (await db.execute(stmt)).all()

    if len(rows) < 5:
        return []

    try:
        import numpy as np
        from umap import UMAP
    except ImportError:
        return []

    embeddings = np.array([list(row.embedding) for row in rows])

    n_neighbors = min(15, len(rows) - 1)
    reducer = UMAP(n_components=2, n_neighbors=n_neighbors, random_state=42)
    coords = reducer.fit_transform(embeddings)

    points = []
    for i, row in enumerate(rows):
        results_list = row.results if isinstance(row.results, list) else (row.results or {}).get("results", [])
        main_cat = results_list[0].get("category_name", "") if results_list else ""

        points.append({
            "id": str(row.id),
            "x": round(float(coords[i][0]), 4),
            "y": round(float(coords[i][1]), 4),
            "label": row.input_text[:60],
            "category": main_cat,
            "confidence": row.overall_confidence,
        })

    return points
