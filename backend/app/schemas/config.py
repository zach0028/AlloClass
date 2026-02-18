from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    description: str = ""
    position: int = 0


class AxisCreate(BaseModel):
    name: str
    description: str = ""
    position: int = 0
    categories: list[CategoryCreate]


class ConfigCreate(BaseModel):
    name: str
    description: str = ""
    template_source: str | None = None
    axes: list[AxisCreate]


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    description: str
    position: int

    model_config = {"from_attributes": True}


class AxisResponse(BaseModel):
    id: UUID
    name: str
    description: str
    position: int
    categories: list[CategoryResponse]

    model_config = {"from_attributes": True}


class ConfigResponse(BaseModel):
    id: UUID
    name: str
    description: str
    template_source: str | None
    created_at: datetime
    updated_at: datetime
    axes: list[AxisResponse]

    model_config = {"from_attributes": True}


class TemplateResponse(BaseModel):
    name: str
    description: str
    axes_count: int
    categories_count: int
