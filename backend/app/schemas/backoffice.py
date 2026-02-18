from uuid import UUID

from pydantic import BaseModel, Field


class ScenarioResponse(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    strategy: str
    difficulty_bias: str


class GenerateRequest(BaseModel):
    config_id: UUID
    count: int = Field(default=10, gt=0, le=200)
    scenario_id: str = "journee-normale"


class DripFeedStartRequest(BaseModel):
    config_id: UUID
    interval_seconds: int = Field(default=10, gt=0)
    total_count: int = Field(default=50, gt=0, le=500)
    scenario_id: str = "journee-normale"


class DripFeedStatusResponse(BaseModel):
    is_running: bool
    generated_count: int
    total_count: int
    interval_seconds: int
    scenario_id: str | None = None


class DeleteTicketsRequest(BaseModel):
    ids: list[UUID] = Field(min_length=1)


class GeneratedTicketResponse(BaseModel):
    id: UUID
    input_text: str
    overall_confidence: float
    was_challenged: bool
    created_at: str | None = None
