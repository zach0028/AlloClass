import json

from app.core.config import settings
from app.core.openai_client import client as openai_client
from app.models.config import Config
from app.prompts.ground_truth import ADAPTIVE_GENERATOR_SYSTEM, ADAPTIVE_GENERATOR_USER
from app.services.prompt_helpers import build_axes_text


async def reformulate_tickets(
    tickets: list[dict],
    config: Config,
    accumulated_rules: list[str],
) -> list[dict]:
    axes_text = build_axes_text(config)
    rules_text = "\n".join(f"- {r}" for r in accumulated_rules) if accumulated_rules else "Aucune regle encore (premier round)."

    tickets_json = json.dumps(
        [{"id": t["classification_id"], "text": t["current_text"]} for t in tickets],
        ensure_ascii=False,
        indent=2,
    )

    response = await openai_client.chat.completions.create(
        model=settings.generator_model,
        messages=[
            {
                "role": "system",
                "content": ADAPTIVE_GENERATOR_SYSTEM.format(
                    axes_and_categories=axes_text,
                    accumulated_rules=rules_text,
                ),
            },
            {
                "role": "user",
                "content": ADAPTIVE_GENERATOR_USER.format(
                    count=len(tickets),
                    tickets_json=tickets_json,
                ),
            },
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    try:
        parsed = json.loads(content)
        reformulations = parsed.get("reformulations", [])
        if isinstance(reformulations, list):
            return reformulations
    except (json.JSONDecodeError, TypeError):
        pass

    return []
