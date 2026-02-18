import random
from pathlib import Path
from typing import Any

import yaml

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "presets" / "scenarios"

_cache: list[dict[str, Any]] | None = None


def _load_all() -> list[dict[str, Any]]:
    global _cache
    if _cache is not None:
        return _cache

    scenarios = []
    for path in sorted(SCENARIOS_DIR.glob("*.yaml")):
        with open(path) as f:
            data = yaml.safe_load(f)
        if data and isinstance(data, dict) and "id" in data:
            scenarios.append(data)

    _cache = scenarios
    return _cache


def get_all_scenarios() -> list[dict[str, Any]]:
    return _load_all()


def get_scenario(scenario_id: str) -> dict[str, Any] | None:
    for s in _load_all():
        if s["id"] == scenario_id:
            return s
    return None


def pick_weighted(pool: list[str], weights: dict[str, float]) -> str:
    items = list(weights.keys())
    w = [weights[k] for k in items]
    total = sum(w)
    if total == 0:
        return random.choice(pool)
    return random.choices(items, weights=w, k=1)[0]


def build_combo_from_scenario(scenario: dict[str, Any], fallback_difficulty: str = "balanced") -> dict[str, str]:
    from app.prompts.blind_generator import (
        PERSONA_POOL,
        SITUATION_POOL_EASY,
        SITUATION_POOL_HARD,
        SITUATION_POOL_MEDIUM,
        STYLE_POOL,
    )

    persona_weights = scenario.get("persona_weights")
    if persona_weights:
        persona = pick_weighted(PERSONA_POOL, persona_weights)
    else:
        persona = random.choice(PERSONA_POOL)

    style_weights = scenario.get("style_weights")
    if style_weights:
        style = pick_weighted(STYLE_POOL, style_weights)
    else:
        style = random.choice(STYLE_POOL)

    situation_overrides = scenario.get("situation_overrides")
    if situation_overrides:
        situation = random.choice(situation_overrides)
    else:
        difficulty = scenario.get("difficulty_bias", fallback_difficulty)
        difficulty_mixes = {
            "easy": (0.7, 0.2, 0.1),
            "balanced": (0.4, 0.4, 0.2),
            "hard": (0.1, 0.3, 0.6),
        }
        easy_w, med_w, _hard_w = difficulty_mixes.get(difficulty, (0.4, 0.4, 0.2))
        roll = random.random()
        if roll < easy_w:
            situation = random.choice(SITUATION_POOL_EASY)
        elif roll < easy_w + med_w:
            situation = random.choice(SITUATION_POOL_MEDIUM)
        else:
            situation = random.choice(SITUATION_POOL_HARD)

    return {"persona": persona, "situation": situation, "style": style}
