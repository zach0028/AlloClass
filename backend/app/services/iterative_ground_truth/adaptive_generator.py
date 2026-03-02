import json

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import generator_llm
from app.schemas.llm_outputs import ReformulationsOutput
from app.models.config import Config
from app.prompts.ground_truth import ADAPTIVE_GENERATOR_SYSTEM, ADAPTIVE_GENERATOR_USER
from app.services.shared.prompt_helpers import build_axes_text


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

    structured_llm = generator_llm.with_structured_output(ReformulationsOutput)
    try:
        result = await structured_llm.ainvoke([
            SystemMessage(content=ADAPTIVE_GENERATOR_SYSTEM.format(
                axes_and_categories=axes_text,
                accumulated_rules=rules_text,
            )),
            HumanMessage(content=ADAPTIVE_GENERATOR_USER.format(
                count=len(tickets),
                tickets_json=tickets_json,
            )),
        ])
        return [r.model_dump() for r in result.reformulations]
    except Exception:
        return []
