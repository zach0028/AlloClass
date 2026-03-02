import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import challenger_llm
from app.models.config import Config
from app.prompts.challenger import CHALLENGER_SYSTEM_PROMPT, CHALLENGER_USER_PROMPT
from app.schemas.llm_outputs import ChallengerOutput
from app.services.shared.prompt_helpers import build_axes_text


async def challenge_classification(
    ticket_text: str,
    initial_results: list[dict],
    weak_axes: list[dict],
    config: Config,
) -> dict:
    axes_text = build_axes_text(config)

    weak_axes_summary = json.dumps(
        [
            {
                "axis_name": wa["axis_name"],
                "category": wa["voted_category_name"],
                "confidence": wa["empirical_confidence"],
            }
            for wa in weak_axes
        ],
        ensure_ascii=False,
        indent=2,
    )

    system_prompt = CHALLENGER_SYSTEM_PROMPT.format(axes_and_categories=axes_text)
    user_prompt = CHALLENGER_USER_PROMPT.format(
        ticket_text=ticket_text,
        initial_results=weak_axes_summary,
    )

    structured_llm = challenger_llm.with_structured_output(ChallengerOutput)
    output = await structured_llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    tokens = 0

    challenges = []
    for ch in output.challenges:
        matching_weak = next(
            (wa for wa in weak_axes if wa["axis_name"] == ch.axis_name),
            None,
        )
        challenges.append({
            "axis_id": matching_weak["axis_id"] if matching_weak else None,
            "axis_name": ch.axis_name,
            "alternative_category": ch.alternative_category,
            "argument": ch.argument,
            "agrees_with_original": ch.agrees_with_original,
            "original_confidence": matching_weak["empirical_confidence"] if matching_weak else 0,
        })

    return {"challenges": challenges, "tokens": tokens}
