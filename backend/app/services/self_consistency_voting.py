import json
from collections import Counter
from uuid import UUID

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.openai_client import client as openai_client
from app.models.config import Config
from app.prompts.classifier import CLASSIFIER_SYSTEM_PROMPT, CLASSIFIER_USER_PROMPT
from app.services.prompt_helpers import build_axes_text, build_few_shot_text


async def _single_classification(
    ticket_text: str,
    config: Config,
    few_shots: list[dict],
    learned_rules_text: str,
) -> dict:
    axes_text = build_axes_text(config)
    few_shot_text = build_few_shot_text(few_shots)

    system_prompt = CLASSIFIER_SYSTEM_PROMPT.format(
        axes_and_categories=axes_text,
        learned_rules=learned_rules_text,
    )
    user_prompt = CLASSIFIER_USER_PROMPT.format(
        few_shot_examples=few_shot_text,
        ticket_text=ticket_text,
    )

    response = await openai_client.chat.completions.create(
        model=settings.classifier_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        reasoning_effort="low",
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    tokens = response.usage.total_tokens if response.usage else 0

    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError) as e:
        parsed = {"results": [], "_parse_error": str(e)}

    return {"parsed": parsed, "tokens": tokens}


async def run_self_consistency(
    ticket_text: str,
    config: Config,
    few_shots: list[dict],
    learned_rules_text: str = "Aucune regle apprise pour le moment.",
    n: int = 3,
) -> dict:
    raw_classifications = []
    total_tokens = 0

    for _ in range(n):
        result = await _single_classification(
            ticket_text, config, few_shots, learned_rules_text
        )
        raw_classifications.append(result["parsed"])
        total_tokens += result["tokens"]

    axis_lookup = {}
    for axis in config.axes:
        cat_lookup = {cat.name: cat.id for cat in axis.categories}
        axis_lookup[axis.name] = {"axis_id": axis.id, "cat_lookup": cat_lookup}

    results_per_axis = []
    for axis in sorted(config.axes, key=lambda a: a.position):
        votes = []
        for classif in raw_classifications:
            for r in classif.get("results", []):
                if r.get("axis_name") == axis.name:
                    votes.append(r.get("category", ""))
                    break

        if not votes:
            continue

        counter = Counter(votes)
        winner, win_count = counter.most_common(1)[0]
        cat_lookup = axis_lookup[axis.name]["cat_lookup"]

        results_per_axis.append({
            "axis_id": str(axis.id),
            "axis_name": axis.name,
            "voted_category_id": str(cat_lookup.get(winner, "")),
            "voted_category_name": winner,
            "vote_count": win_count,
            "empirical_confidence": round(win_count / len(votes), 2),
            "all_votes": votes,
        })

    return {
        "results_per_axis": results_per_axis,
        "raw_classifications": raw_classifications,
        "total_tokens": total_tokens,
    }


async def compute_axis_disagreement(
    config_id: UUID, db: AsyncSession
) -> list[dict]:
    query = sa_text("""
        SELECT
            cr.vote_details,
            cr.config_id
        FROM classification_results cr
        WHERE cr.config_id = :config_id
            AND cr.vote_details IS NOT NULL
    """)
    result = await db.execute(query, {"config_id": str(config_id)})
    rows = result.fetchall()

    if not rows:
        return []

    from app.services.config_management import get_config_with_relations
    config = await get_config_with_relations(config_id, db)

    axis_stats: dict[str, dict] = {}
    for axis in config.axes:
        axis_stats[axis.name] = {
            "axis_id": str(axis.id),
            "axis_name": axis.name,
            "total": 0,
            "disagreements": 0,
            "pair_counts": Counter(),
        }

    for row in rows:
        vote_details = row.vote_details
        if not vote_details or "results_per_axis" not in vote_details:
            continue
        for axis_result in vote_details["results_per_axis"]:
            axis_name = axis_result.get("axis_name")
            if axis_name not in axis_stats:
                continue
            votes = axis_result.get("all_votes", [])
            if not votes:
                continue

            axis_stats[axis_name]["total"] += 1
            unique_votes = set(votes)
            if len(unique_votes) > 1:
                axis_stats[axis_name]["disagreements"] += 1
                sorted_pair = tuple(sorted(unique_votes))
                axis_stats[axis_name]["pair_counts"][sorted_pair] += 1

    output = []
    for axis_name, stats in axis_stats.items():
        total = stats["total"]
        if total == 0:
            continue
        disagreement_rate = round(stats["disagreements"] / total, 3)
        worst_pairs = [
            (pair[0], pair[1], round(count / total, 3))
            for pair, count in stats["pair_counts"].most_common(3)
        ]
        suggested_threshold = 0.75
        if disagreement_rate > 0.25:
            suggested_threshold = min(0.90, 0.75 + (disagreement_rate - 0.25) * 0.5)

        output.append({
            "axis_id": stats["axis_id"],
            "axis_name": axis_name,
            "disagreement_rate": disagreement_rate,
            "worst_pairs": worst_pairs,
            "suggested_threshold": round(suggested_threshold, 2),
            "sample_size": total,
        })

    return output
