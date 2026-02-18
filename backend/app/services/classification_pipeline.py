import asyncio
import time
from collections.abc import AsyncGenerator
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.classification_result import ClassificationResult
from app.models.config import Config
from app.services.challenger_analysis import challenge_classification
from app.services.learning_explainer import get_active_learned_rules
from app.services.prompt_helpers import build_learned_rules_text
from app.services.self_consistency_voting import run_self_consistency
from app.services.vector_search import compute_embedding, search_similar_feedbacks


def _build_results_jsonb(vote_results: list[dict], config: Config) -> list[dict]:
    axis_lookup = {}
    for axis in config.axes:
        cat_lookup = {cat.name: str(cat.id) for cat in axis.categories}
        axis_lookup[axis.name] = {"axis_id": str(axis.id), "cat_lookup": cat_lookup}

    results = []
    for vr in vote_results:
        axis_name = vr["axis_name"]
        cat_name = vr["voted_category_name"]
        info = axis_lookup.get(axis_name, {})
        results.append({
            "axis_id": info.get("axis_id", ""),
            "axis_name": axis_name,
            "category_id": info.get("cat_lookup", {}).get(cat_name, ""),
            "category_name": cat_name,
            "confidence": vr["empirical_confidence"],
            "vote_count": vr["vote_count"],
            "all_votes": vr["all_votes"],
        })
    return results


async def _run_pipeline(
    text: str,
    config: Config,
    db: AsyncSession,
    on_step: Callable[[str, str], None] | None = None,
) -> ClassificationResult:
    start = time.perf_counter()
    total_tokens = 0

    if on_step:
        on_step("embedding", "Calcul embedding...")
    embedding = await compute_embedding(text)

    if on_step:
        on_step("few_shot", "Recherche exemples similaires...")
    few_shots = await search_similar_feedbacks(embedding, config.id, db)
    if on_step:
        on_step("few_shot", f"{len(few_shots)} exemple(s) trouve(s)")

    learned_rules = await get_active_learned_rules(config.id, db)
    learned_rules_text = build_learned_rules_text(learned_rules)

    if on_step:
        on_step("classification", "Classification multi-axes en cours...")
    vote_result = await run_self_consistency(
        ticket_text=text,
        config=config,
        few_shots=few_shots,
        learned_rules_text=learned_rules_text,
        n=settings.self_consistency_n,
    )
    total_tokens += vote_result.get("total_tokens", 0)

    results_per_axis = vote_result["results_per_axis"]
    results_jsonb = _build_results_jsonb(results_per_axis, config)

    if on_step:
        unanimous = all(r["empirical_confidence"] == 1.0 for r in results_per_axis)
        msg = "Vote unanime sur tous les axes" if unanimous else "Desaccord sur certains axes"
        on_step("self_consistency", msg)

    overall_confidence = 0.0
    if results_per_axis:
        overall_confidence = round(
            sum(r["empirical_confidence"] for r in results_per_axis) / len(results_per_axis),
            3,
        )

    weak_axes = []
    for vr in results_per_axis:
        axis = next((a for a in config.axes if str(a.id) == vr["axis_id"]), None)
        threshold = axis.challenger_threshold if axis else settings.challenger_threshold
        if vr["empirical_confidence"] < threshold:
            weak_axes.append(vr)

    challenger_response_data = None
    was_challenged = False
    if weak_axes:
        was_challenged = True
        if on_step:
            axes_names = ", ".join(wa["axis_name"] for wa in weak_axes)
            on_step("challenger", f"Challenger active sur : {axes_names}")

        challenger_result = await challenge_classification(
            ticket_text=text,
            initial_results=results_per_axis,
            weak_axes=weak_axes,
            config=config,
        )
        challenger_response_data = challenger_result["challenges"]
        total_tokens += challenger_result["tokens"]

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    classification = ClassificationResult(
        config_id=config.id,
        input_text=text,
        results=results_jsonb,
        overall_confidence=overall_confidence,
        was_challenged=was_challenged,
        challenger_response=challenger_response_data,
        model_used=settings.classifier_model,
        tokens_used=total_tokens,
        processing_time_ms=elapsed_ms,
        vote_details=vote_result,
        embedding=embedding,
    )
    db.add(classification)
    await db.commit()
    await db.refresh(classification)

    return classification


async def classify_ticket(
    text: str, config: Config, db: AsyncSession
) -> ClassificationResult:
    return await _run_pipeline(text, config, db)


async def classify_ticket_stream(
    text: str, config: Config, db: AsyncSession
) -> AsyncGenerator[dict, None]:
    steps: list[dict] = []

    def collect_step(step: str, message: str) -> None:
        steps.append({"type": "step", "data": {"step": step, "message": message}})

    classification = await _run_pipeline(text, config, db, on_step=collect_step)

    for s in steps:
        yield s

    yield {
        "type": "result",
        "data": {
            "classification_id": str(classification.id),
            "results": classification.results,
            "overall_confidence": classification.overall_confidence,
            "was_challenged": classification.was_challenged,
            "challenger_response": classification.challenger_response,
            "processing_time_ms": classification.processing_time_ms,
        },
    }


async def classify_batch(
    texts: list[str], config: Config, db: AsyncSession, concurrency: int = 3
) -> list[ClassificationResult]:
    semaphore = asyncio.Semaphore(concurrency)
    results: list[ClassificationResult | None] = [None] * len(texts)

    async def _classify_one(index: int, ticket_text: str) -> None:
        async with semaphore:
            results[index] = await classify_ticket(ticket_text, config, db)

    await asyncio.gather(*[
        _classify_one(i, t) for i, t in enumerate(texts)
    ])

    return [r for r in results if r is not None]
