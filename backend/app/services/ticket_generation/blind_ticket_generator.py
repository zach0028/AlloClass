import asyncio
import random
from uuid import UUID

from app.core.config import settings
from app.core.database import async_session
from app.core.openai_client import client as openai_client
from app.models.config import Config
from app.prompts.blind_generator import (
    BLIND_GENERATOR_SYSTEM_PROMPT,
    BLIND_GENERATOR_USER_PROMPT,
    PERSONA_POOL,
    SITUATION_POOL_EASY,
    SITUATION_POOL_HARD,
    SITUATION_POOL_MEDIUM,
    STYLE_POOL,
)
from app.services.scenario_loader import build_combo_from_scenario, get_scenario

DIFFICULTY_MIXES = {
    "easy": (0.7, 0.2, 0.1),
    "balanced": (0.4, 0.4, 0.2),
    "hard": (0.1, 0.3, 0.6),
}


def _pick_situation(difficulty_mix: str) -> str:
    easy_w, med_w, hard_w = DIFFICULTY_MIXES.get(difficulty_mix, (0.4, 0.4, 0.2))
    roll = random.random()
    if roll < easy_w:
        return random.choice(SITUATION_POOL_EASY)
    if roll < easy_w + med_w:
        return random.choice(SITUATION_POOL_MEDIUM)
    return random.choice(SITUATION_POOL_HARD)


async def generate_blind_tickets(
    config: Config,
    count: int = 10,
    difficulty_mix: str = "balanced",
    scenario_id: str | None = None,
) -> list[str]:
    scenario = get_scenario(scenario_id) if scenario_id else None

    combos = []
    for _ in range(count):
        if scenario:
            combos.append(build_combo_from_scenario(scenario, difficulty_mix))
        else:
            combos.append({
                "persona": random.choice(PERSONA_POOL),
                "situation": _pick_situation(difficulty_mix),
                "style": random.choice(STYLE_POOL),
            })

    batch_size = 5
    tickets: list[str] = []

    for i in range(0, len(combos), batch_size):
        batch = combos[i : i + batch_size]
        tasks = [_generate_one(combo) for combo in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, str) and r.strip():
                tickets.append(r.strip())

    return tickets


async def _generate_one(combo: dict) -> str:
    response = await openai_client.chat.completions.create(
        model=settings.generator_model,
        messages=[
            {"role": "system", "content": BLIND_GENERATOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": BLIND_GENERATOR_USER_PROMPT.format(**combo),
            },
        ],
        temperature=1.0,
        max_tokens=500,
    )
    return response.choices[0].message.content or ""


class DripFeedManager:
    def __init__(self):
        self.is_running: bool = False
        self.generated_count: int = 0
        self.total_count: int = 0
        self.interval_seconds: int = 10
        self.config_id: UUID | None = None
        self.scenario_id: str | None = None
        self._task: asyncio.Task | None = None

    async def start(
        self,
        config_id: UUID,
        interval_seconds: int = 10,
        total_count: int = 50,
        scenario_id: str | None = None,
    ):
        if self.is_running:
            return

        self.config_id = config_id
        self.interval_seconds = interval_seconds
        self.total_count = total_count
        self.scenario_id = scenario_id
        self.generated_count = 0
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())

    async def _run_loop(self):
        from app.services.classification_pipeline import classify_ticket
        from app.services.config_management import get_config_with_relations

        try:
            while self.is_running and self.generated_count < self.total_count:
                async with async_session() as db:
                    config = await get_config_with_relations(self.config_id, db)
                    tickets = await generate_blind_tickets(
                        config, count=1, scenario_id=self.scenario_id
                    )
                    if tickets:
                        await classify_ticket(tickets[0], config, db)
                        self.generated_count += 1

                await asyncio.sleep(self.interval_seconds)
        except asyncio.CancelledError:
            pass
        finally:
            self.is_running = False

    async def stop(self):
        if self._task:
            self._task.cancel()
            self.is_running = False
            self.config_id = None
            self.scenario_id = None

    def get_status(self) -> dict:
        return {
            "is_running": self.is_running,
            "generated_count": self.generated_count,
            "total_count": self.total_count,
            "interval_seconds": self.interval_seconds,
            "config_id": str(self.config_id) if self.config_id else None,
            "scenario_id": self.scenario_id,
        }


drip_feed_manager = DripFeedManager()
