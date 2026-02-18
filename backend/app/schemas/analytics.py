from uuid import UUID

from pydantic import BaseModel, Field


class KPIResponse(BaseModel):
    total_classifications: int
    average_confidence: float = Field(ge=0, le=1)
    challenge_rate: float = Field(ge=0, le=1)
    feedback_count: int


class ConfidenceBucket(BaseModel):
    range_start: float = Field(ge=0, le=1)
    range_end: float = Field(ge=0, le=1)
    count: int


class ConfidenceResponse(BaseModel):
    buckets: list[ConfidenceBucket]


class AxisStatsResponse(BaseModel):
    axis_id: UUID
    axis_name: str
    accuracy: float = Field(ge=0, le=1)
    most_confused_pair: list[str] | None
    category_distribution: dict[str, int]


class EmbeddingPoint(BaseModel):
    x: float
    y: float
    label: str
    category: str
    confidence: float = Field(ge=0, le=1)


class EmbeddingMapResponse(BaseModel):
    points: list[EmbeddingPoint]


class MatrixAxis(BaseModel):
    name: str
    categories: list[str]


class MatrixCell(BaseModel):
    x_category: str
    y_category: str
    count: int
    avg_confidence: float = Field(ge=0, le=1)


class ClassificationMatrixResponse(BaseModel):
    axes: list[MatrixAxis]
    x_axis: str
    y_axis: str
    cells: list[MatrixCell]
    total: int
