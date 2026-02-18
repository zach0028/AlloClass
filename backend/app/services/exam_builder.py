import json
from uuid import UUID

from app.core.config import settings
from app.core.openai_client import client as openai_client
from app.models.config import Config
from app.prompts.exam_builder import (
    ADVERSARIAL_PROMPT,
    EXAM_BUILDER_SYSTEM_PROMPT,
)
from app.services.prompt_helpers import build_axes_text


async def generate_adversarial_cases(
    config: Config,
    target_axes: list[UUID] | None = None,
    count: int = 20,
) -> list[dict]:
    axes_text = build_axes_text(config)

    if target_axes:
        target_names = [
            a.name for a in config.axes if a.id in target_axes
        ]
    else:
        target_names = [a.name for a in config.axes]

    response = await openai_client.chat.completions.create(
        model=settings.generator_model,
        messages=[
            {
                "role": "system",
                "content": EXAM_BUILDER_SYSTEM_PROMPT.format(
                    axes_and_categories=axes_text,
                ),
            },
            {
                "role": "user",
                "content": ADVERSARIAL_PROMPT.format(
                    count=count,
                    target_axes=", ".join(target_names),
                ),
            },
        ],
        temperature=1.0,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            for key in ("cases", "test_cases", "tickets", "adversarial_cases"):
                if key in parsed and isinstance(parsed[key], list):
                    parsed = parsed[key]
                    break
            else:
                vals = [v for v in parsed.values() if isinstance(v, list)]
                parsed = vals[0] if vals else []
        if not isinstance(parsed, list):
            parsed = []
    except (json.JSONDecodeError, TypeError):
        parsed = []

    return parsed[:count]
