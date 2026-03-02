import asyncio
from collections.abc import AsyncGenerator
from operator import add
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.classification_result import ClassificationResult
from app.models.config import Config
from app.models.evaluation_result import EvaluationResult

from .adaptive_generator import reformulate_tickets
from .judge import apply_rule_updates, evaluate_round

MAX_ROUNDS_SAFETY = 15
EARLY_STOP_DELTA = 0.01


class GroundTruthState(TypedDict):
    config: Any
    target_confidence: float
    max_rounds: int
    ticket_data: list[dict]
    frozen_ids: list[str]
    frozen_results: dict[str, dict]
    accumulated_rules: list[str]
    prompt_evolution: list[dict]
    round_num: int
    prev_active_avg: float
    all_round_results: list[list[dict]]
    reform_map: dict[str, str]
    active_results: list[dict]
    events: Annotated[list[dict], add]
    done_data: dict | None


async def _reformulate_node(state: GroundTruthState) -> dict:
    config = state["config"]
    ticket_data = state["ticket_data"]
    accumulated_rules = state["accumulated_rules"]
    frozen_ids = state["frozen_ids"]
    frozen_results = state["frozen_results"]
    round_num = state["round_num"]

    active_tickets = [
        td for td in ticket_data if td["classification_id"] not in frozen_ids
    ]
    events = []

    events.append({
        "type": "round_start",
        "data": {
            "round": round_num,
            "rules_count": len(accumulated_rules),
            "active_tickets": len(active_tickets),
            "frozen_tickets": len(frozen_ids),
        },
    })

    for cid in frozen_ids:
        fr = frozen_results[cid]
        events.append({
            "type": "ticket_result",
            "data": {
                "round": round_num,
                "classification_id": cid,
                "reformulated_text": fr["reformulated_text"][:150],
                "confidence": fr["confidence"],
                "results_per_axis": fr["results_per_axis"],
                "used_fallback": False,
                "frozen": True,
            },
        })

    events.append({
        "type": "phase",
        "data": {"phase": "reformulating", "status": "start", "round": round_num},
    })

    try:
        reformulations = await reformulate_tickets(
            active_tickets, config, accumulated_rules
        )
    except Exception as exc:
        events.append({
            "type": "phase",
            "data": {"phase": "reformulating", "status": "done", "round": round_num},
        })
        events.append({
            "type": "round_error",
            "data": {
                "round": round_num,
                "phase": "reformulating",
                "error": str(exc),
            },
        })
        reformulations = []
    else:
        events.append({
            "type": "phase",
            "data": {"phase": "reformulating", "status": "done", "round": round_num},
        })

    reform_map = {r["id"]: r["reformulated_text"] for r in reformulations}
    return {"events": events, "reform_map": reform_map}


async def _classify_node(state: GroundTruthState) -> dict:
    config = state["config"]
    ticket_data = state["ticket_data"]
    frozen_ids = state["frozen_ids"]
    frozen_results = state["frozen_results"]
    reform_map = state["reform_map"]
    round_num = state["round_num"]

    active_tickets = [
        td for td in ticket_data if td["classification_id"] not in frozen_ids
    ]
    events = []

    total = len(active_tickets)
    events.append({
        "type": "phase",
        "data": {
            "phase": "classifying",
            "status": "start",
            "round": round_num,
            "detail": f"0/{total}",
        },
    })

    async def _classify_one(td: dict) -> dict:
        cid = td["classification_id"]
        reformulated_text = reform_map.get(cid)
        used_fallback = reformulated_text is None
        if used_fallback:
            reformulated_text = td["current_text"]
        try:
            async with async_session() as classify_db:
                from app.services.classification.classification_pipeline import (
                    classify_ticket,
                )

                classification = await classify_ticket(
                    reformulated_text, config, classify_db
                )
            results_per_axis = [
                {
                    "axis_name": r["axis_name"],
                    "category_name": r["category_name"],
                    "confidence": r["confidence"],
                }
                for r in (classification.results or [])
            ]
            td["current_text"] = reformulated_text
            return {
                "classification_id": cid,
                "original_text": td["original_text"],
                "reformulated_text": reformulated_text,
                "confidence": classification.overall_confidence,
                "results_per_axis": results_per_axis,
                "used_fallback": used_fallback,
                "error": None,
            }
        except Exception as exc:
            return {
                "classification_id": cid,
                "original_text": td["original_text"],
                "reformulated_text": reformulated_text or td["current_text"],
                "confidence": 0.0,
                "results_per_axis": [],
                "used_fallback": used_fallback,
                "error": str(exc),
            }

    active_results = list(
        await asyncio.gather(*[_classify_one(td) for td in active_tickets])
    )

    for result in active_results:
        cid = result["classification_id"]
        if result["error"]:
            events.append({
                "type": "ticket_error",
                "data": {
                    "round": round_num,
                    "classification_id": cid,
                    "error": result["error"],
                },
            })
        else:
            events.append({
                "type": "ticket_result",
                "data": {
                    "round": round_num,
                    "classification_id": cid,
                    "reformulated_text": result["reformulated_text"][:150],
                    "confidence": result["confidence"],
                    "results_per_axis": result["results_per_axis"],
                    "used_fallback": result["used_fallback"],
                    "frozen": False,
                },
            })

    events.append({
        "type": "phase",
        "data": {"phase": "classifying", "status": "done", "round": round_num},
    })

    round_results = active_results + [frozen_results[cid] for cid in frozen_ids]
    all_round_results = state["all_round_results"] + [round_results]

    return {
        "events": events,
        "all_round_results": all_round_results,
        "active_results": active_results,
    }


async def _evaluate_node(state: GroundTruthState) -> dict:
    config = state["config"]
    round_num = state["round_num"]
    active_results = state["active_results"]
    target_confidence = state["target_confidence"]
    accumulated_rules = state["accumulated_rules"]
    frozen_ids = list(state["frozen_ids"])
    frozen_results = dict(state["frozen_results"])

    all_results = active_results + [
        frozen_results[cid] for cid in state["frozen_ids"]
    ]
    avg_confidence = sum(r["confidence"] for r in all_results) / len(all_results)
    active_avg = (
        sum(r["confidence"] for r in active_results) / len(active_results)
        if active_results
        else 0.0
    )
    above_threshold = sum(
        1 for r in all_results if r["confidence"] >= target_confidence
    )

    events = []
    events.append({
        "type": "phase",
        "data": {"phase": "evaluating", "status": "start", "round": round_num},
    })

    try:
        judge_result = await evaluate_round(
            round_number=round_num,
            round_results=list(active_results),
            config=config,
            current_rules=accumulated_rules,
            target_confidence=target_confidence,
        )
    except Exception as exc:
        events.append({
            "type": "phase",
            "data": {"phase": "evaluating", "status": "done", "round": round_num},
        })
        events.append({
            "type": "round_error",
            "data": {"round": round_num, "phase": "evaluating", "error": str(exc)},
        })
        judge_result = {
            "ticket_evaluations": [],
            "rules_to_add": [],
            "rules_to_remove": [],
            "rules_to_modify": [],
            "global_diagnosis": f"Le juge a echoue ce round : {exc}",
        }
    else:
        events.append({
            "type": "phase",
            "data": {"phase": "evaluating", "status": "done", "round": round_num},
        })

    new_rules = apply_rule_updates(accumulated_rules, judge_result)

    prompt_evolution = state["prompt_evolution"] + [{
        "round": round_num,
        "rules_added": judge_result.get("rules_to_add", []),
        "rules_removed": judge_result.get("rules_to_remove", []),
        "rules_modified": judge_result.get("rules_to_modify", []),
    }]

    for result in active_results:
        if not result["error"] and result["confidence"] >= target_confidence:
            cid = result["classification_id"]
            if cid not in frozen_ids:
                frozen_ids.append(cid)
                frozen_results[cid] = result

    events.append({
        "type": "round_complete",
        "data": {
            "round": round_num,
            "avg_confidence": round(avg_confidence, 3),
            "above_threshold": above_threshold,
            "total_tickets": len(all_results),
            "frozen_tickets": len(frozen_ids),
            "rules_added": judge_result.get("rules_to_add", []),
            "rules_removed": judge_result.get("rules_to_remove", []),
            "rules_modified": judge_result.get("rules_to_modify", []),
            "accumulated_rules": new_rules,
            "diagnosis": judge_result.get("global_diagnosis", ""),
            "ticket_evaluations": judge_result.get("ticket_evaluations", []),
        },
    })

    done_data = None
    if above_threshold == len(all_results):
        done_data = {
            "reason": "target_reached",
            "rounds_completed": round_num,
            "final_avg_confidence": round(avg_confidence, 3),
            "message": (
                f"Tous les tickets ont atteint {target_confidence:.0%} "
                f"de confiance en {round_num} round(s)."
            ),
        }
    elif round_num > 1 and abs(active_avg - state["prev_active_avg"]) < EARLY_STOP_DELTA:
        done_data = {
            "reason": "early_stop",
            "rounds_completed": round_num,
            "final_avg_confidence": round(avg_confidence, 3),
            "message": (
                f"Convergence detectee (delta < {EARLY_STOP_DELTA:.0%}). "
                "Les tickets restants revelent probablement un chevauchement "
                "entre categories."
            ),
            "diagnosis": judge_result.get("global_diagnosis", ""),
        }

    return {
        "events": events,
        "accumulated_rules": new_rules,
        "prompt_evolution": prompt_evolution,
        "frozen_ids": frozen_ids,
        "frozen_results": frozen_results,
        "round_num": round_num + 1,
        "prev_active_avg": active_avg,
        "done_data": done_data,
    }


def _should_continue(state: GroundTruthState) -> str:
    if state["done_data"]:
        return END
    active = [
        td
        for td in state["ticket_data"]
        if td["classification_id"] not in state["frozen_ids"]
    ]
    if not active:
        return END
    if state["round_num"] > state["max_rounds"]:
        return END
    return "reformulate"


_graph_builder = StateGraph(GroundTruthState)
_graph_builder.add_node("reformulate", _reformulate_node)
_graph_builder.add_node("classify", _classify_node)
_graph_builder.add_node("evaluate", _evaluate_node)
_graph_builder.add_edge("reformulate", "classify")
_graph_builder.add_edge("classify", "evaluate")
_graph_builder.add_conditional_edges(
    "evaluate", _should_continue, {"reformulate": "reformulate", END: END}
)
_graph_builder.set_entry_point("reformulate")
ground_truth_graph = _graph_builder.compile()


async def _select_low_confidence_tickets(
    config_id, db: AsyncSession, count: int
) -> list[ClassificationResult]:
    result = await db.execute(
        select(ClassificationResult)
        .where(ClassificationResult.config_id == config_id)
        .order_by(ClassificationResult.overall_confidence.asc())
        .limit(count)
    )
    return list(result.scalars().all())


async def run_ground_truth_loop(
    config: Config,
    db: AsyncSession,
    ticket_count: int = 5,
    max_rounds: int | None = 5,
    target_confidence: float = 0.9,
) -> AsyncGenerator[dict, None]:
    effective_max = max_rounds or MAX_ROUNDS_SAFETY

    tickets = await _select_low_confidence_tickets(config.id, db, ticket_count)
    if not tickets:
        yield {
            "type": "error",
            "data": {"message": "Aucun ticket classifie disponible."},
        }
        return

    ticket_data = [
        {
            "classification_id": str(t.id),
            "original_text": t.input_text,
            "current_text": t.input_text,
            "original_confidence": t.overall_confidence,
        }
        for t in tickets
    ]

    yield {
        "type": "init",
        "data": {
            "ticket_count": len(ticket_data),
            "max_rounds": effective_max,
            "target_confidence": target_confidence,
            "tickets": [
                {
                    "classification_id": td["classification_id"],
                    "original_text": td["original_text"][:100],
                    "original_confidence": td["original_confidence"],
                }
                for td in ticket_data
            ],
        },
    }

    initial_state: GroundTruthState = {
        "config": config,
        "target_confidence": target_confidence,
        "max_rounds": effective_max,
        "ticket_data": ticket_data,
        "frozen_ids": [],
        "frozen_results": {},
        "accumulated_rules": [],
        "prompt_evolution": [],
        "round_num": 1,
        "prev_active_avg": 0.0,
        "all_round_results": [],
        "reform_map": {},
        "active_results": [],
        "events": [],
        "done_data": None,
    }

    events_yielded = 0
    final_state = initial_state

    async for state_snapshot in ground_truth_graph.astream(
        initial_state, stream_mode="values"
    ):
        new_events = state_snapshot["events"][events_yielded:]
        for event in new_events:
            yield event
        events_yielded = len(state_snapshot["events"])
        final_state = state_snapshot

    done_data = final_state.get("done_data")
    if not done_data:
        frozen_count = len(final_state["frozen_ids"])
        total = len(ticket_data)
        last_round = final_state["round_num"] - 1

        if frozen_count > 0:
            final_avg = (
                sum(
                    final_state["frozen_results"][cid]["confidence"]
                    for cid in final_state["frozen_ids"]
                )
                / total
            )
        else:
            final_avg = final_state["prev_active_avg"]

        done_data = {
            "reason": "all_frozen" if frozen_count == total else "max_rounds",
            "rounds_completed": last_round,
            "final_avg_confidence": round(final_avg, 3),
            "message": (
                f"Tous les tickets ont atteint le seuil en {last_round} round(s)."
                if frozen_count == total
                else f"Maximum de {effective_max} rounds atteint."
            ),
        }

    yield {"type": "done", "data": done_data}

    await _persist_results(
        config,
        db,
        effective_max,
        target_confidence,
        ticket_data,
        final_state["all_round_results"],
        final_state["accumulated_rules"],
        final_state["prompt_evolution"],
        done_data,
    )


async def _persist_results(
    config: Config,
    db: AsyncSession,
    max_rounds: int,
    target_confidence: float,
    ticket_data: list[dict],
    all_round_results: list[list[dict]],
    accumulated_rules: list[str],
    prompt_evolution: list[dict],
    done_data: dict,
) -> None:
    ticket_trajectories = []
    for td in ticket_data:
        cid = td["classification_id"]
        rounds = []
        for round_results in all_round_results:
            for rr in round_results:
                if rr["classification_id"] == cid:
                    rounds.append({
                        "reformulation": rr["reformulated_text"][:300],
                        "confidence": rr["confidence"],
                        "results_per_axis": rr.get("results_per_axis", []),
                    })
                    break

        ticket_trajectories.append({
            "classification_id": cid,
            "original_text": td["original_text"][:300],
            "original_confidence": td["original_confidence"],
            "final_confidence": (
                rounds[-1]["confidence"] if rounds else td["original_confidence"]
            ),
            "converged": (
                (rounds[-1]["confidence"] if rounds else 0) >= target_confidence
            ),
            "rounds": rounds,
        })

    evaluation = EvaluationResult(
        config_id=config.id,
        eval_type="ground_truth",
        results={
            "max_rounds": max_rounds,
            "target_confidence": target_confidence,
            "ticket_trajectories": ticket_trajectories,
            "prompt_evolution": prompt_evolution,
            "accumulated_rules": accumulated_rules,
            "done": done_data,
        },
        overall_accuracy=done_data.get("final_avg_confidence"),
    )
    db.add(evaluation)
    await db.commit()
