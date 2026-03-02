from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import generator_llm
from app.models.config import Config
from app.prompts.exam_builder import (
    ADVERSARIAL_PROMPT,
    EXAM_BUILDER_SYSTEM_PROMPT,
)
from app.schemas.llm_outputs import AdversarialCasesOutput
from app.services.shared.prompt_helpers import build_axes_text


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

    structured_llm = generator_llm.with_structured_output(AdversarialCasesOutput)
    result = await structured_llm.ainvoke([
        SystemMessage(
            content=EXAM_BUILDER_SYSTEM_PROMPT.format(
                axes_and_categories=axes_text,
            )
        ),
        HumanMessage(
            content=ADVERSARIAL_PROMPT.format(
                count=count,
                target_axes=", ".join(target_names),
            )
        ),
    ])

    return [c.model_dump() for c in result.cases[:count]]
