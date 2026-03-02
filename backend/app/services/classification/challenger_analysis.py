import json

from app.core.config import settings
from app.core.openai_client import client as openai_client
from app.models.config import Config
from app.prompts.challenger import CHALLENGER_SYSTEM_PROMPT, CHALLENGER_USER_PROMPT
from app.services.prompt_helpers import build_axes_text


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

    response = await openai_client.chat.completions.create(
        model=settings.challenger_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        reasoning_effort="medium",
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    tokens = response.usage.total_tokens if response.usage else 0

    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        parsed = {"challenges": []}

    challenges = []
    for ch in parsed.get("challenges", []):
        matching_weak = next(
            (wa for wa in weak_axes if wa["axis_name"] == ch.get("axis_name")),
            None,
        )
        challenges.append({
            "axis_id": matching_weak["axis_id"] if matching_weak else None,
            "axis_name": ch.get("axis_name", ""),
            "alternative_category": ch.get("alternative_category", ""),
            "argument": ch.get("argument", ""),
            "agrees_with_original": ch.get("agrees_with_original", True),
            "original_confidence": matching_weak["empirical_confidence"] if matching_weak else 0,
        })

    return {"challenges": challenges, "tokens": tokens}
