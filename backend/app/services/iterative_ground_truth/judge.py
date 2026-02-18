import json

from app.core.config import settings
from app.core.openai_client import client as openai_client
from app.models.config import Config
from app.prompts.ground_truth import JUDGE_SYSTEM, JUDGE_USER
from app.services.prompt_helpers import build_axes_text


async def evaluate_round(
    round_number: int,
    round_results: list[dict],
    config: Config,
    current_rules: list[str],
    target_confidence: float,
) -> dict:
    axes_text = build_axes_text(config)

    if current_rules:
        rules_text = "\n".join(f"[{i}] {r}" for i, r in enumerate(current_rules))
    else:
        rules_text = "Aucune regle encore."

    avg_confidence = sum(r["confidence"] for r in round_results) / len(round_results) if round_results else 0
    above = sum(1 for r in round_results if r["confidence"] >= target_confidence)

    results_json = json.dumps(
        [
            {
                "classification_id": r["classification_id"],
                "original_text": r["original_text"][:200],
                "reformulated_text": r["reformulated_text"][:200],
                "confidence": r["confidence"],
                "results_per_axis": r.get("results_per_axis", []),
            }
            for r in round_results
        ],
        ensure_ascii=False,
        indent=2,
    )

    response = await openai_client.chat.completions.create(
        model=settings.evaluator_model,
        messages=[
            {
                "role": "system",
                "content": JUDGE_SYSTEM.format(
                    axes_and_categories=axes_text,
                    current_rules=rules_text,
                ),
            },
            {
                "role": "user",
                "content": JUDGE_USER.format(
                    round_number=round_number,
                    avg_confidence=avg_confidence,
                    target_confidence=target_confidence,
                    above_threshold=above,
                    total_tickets=len(round_results),
                    results_json=results_json,
                ),
            },
        ],
        reasoning_effort="low",
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    try:
        parsed = json.loads(content)
        return {
            "ticket_evaluations": parsed.get("ticket_evaluations", []),
            "rules_to_add": parsed.get("rules_to_add", []),
            "rules_to_remove": parsed.get("rules_to_remove", []),
            "rules_to_modify": parsed.get("rules_to_modify", []),
            "global_diagnosis": parsed.get("global_diagnosis", ""),
        }
    except (json.JSONDecodeError, TypeError):
        return {
            "ticket_evaluations": [],
            "rules_to_add": [],
            "rules_to_remove": [],
            "rules_to_modify": [],
            "global_diagnosis": "Erreur lors de l'analyse du juge.",
        }


def apply_rule_updates(
    current_rules: list[str],
    judge_result: dict,
) -> list[str]:
    rules = list(current_rules)

    indices_to_remove: set[int] = set()
    for item in judge_result.get("rules_to_remove", []):
        if isinstance(item, int) and 0 <= item < len(rules):
            indices_to_remove.add(item)
        elif isinstance(item, str):
            for i, r in enumerate(rules):
                if r.strip().lower() == item.strip().lower():
                    indices_to_remove.add(i)
                    break

    for modification in judge_result.get("rules_to_modify", []):
        idx = modification.get("index")
        new_text = modification.get("new_rule", "")
        if isinstance(idx, int) and 0 <= idx < len(rules) and new_text:
            rules[idx] = new_text
        else:
            old = modification.get("old_rule", "")
            if old and new_text:
                for i, r in enumerate(rules):
                    if r.strip().lower() == old.strip().lower():
                        rules[i] = new_text
                        break

    rules = [r for i, r in enumerate(rules) if i not in indices_to_remove]

    for rule_text in judge_result.get("rules_to_add", []):
        if rule_text and rule_text not in rules:
            rules.append(rule_text)

    return rules
