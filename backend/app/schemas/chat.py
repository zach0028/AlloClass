from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    config_id: UUID
    conversation_id: UUID | None = None


class ChatMessageResponse(BaseModel):
    id: UUID
    config_id: UUID
    conversation_id: UUID | None
    role: Literal["user", "assistant", "system"]
    content: str
    intent: str | None
    metadata_: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    config_id: UUID
    title: str | None = None


class ConversationResponse(BaseModel):
    id: UUID
    config_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: str | None = None

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
