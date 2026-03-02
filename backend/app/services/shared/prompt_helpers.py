from app.models.config import Config
from app.models.learned_rule import LearnedRule
from app.prompts.classifier import CLASSIFIER_FEW_SHOT_TEMPLATE


def build_axes_text(config: Config) -> str:
    lines = []
    for axis in sorted(config.axes, key=lambda a: a.position):
        lines.append(f"\n### {axis.name}")
        if axis.description:
            lines.append(f"  {axis.description}")
        for cat in sorted(axis.categories, key=lambda c: c.position):
            lines.append(f"  - {cat.name} : {cat.description}")
    return "\n".join(lines)


def build_few_shot_text(few_shots: list[dict]) -> str:
    if not few_shots:
        return "Aucun exemple similaire disponible."
    return "\n".join(
        CLASSIFIER_FEW_SHOT_TEMPLATE.format(index=i + 1, **fs)
        for i, fs in enumerate(few_shots)
    )


def build_learned_rules_text(rules: list[LearnedRule]) -> str:
    if not rules:
        return "Aucune regle apprise pour le moment."
    lines = []
    for i, rule in enumerate(rules, 1):
        lines.append(f"{i}. {rule.rule_text}")
    return "\n".join(lines)
