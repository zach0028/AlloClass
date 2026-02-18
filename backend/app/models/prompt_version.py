import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("configs.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    change_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    change_description: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    prompt_snapshot: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )
    learned_rules_snapshot: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )
    challenger_thresholds_snapshot: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )
    accuracy_at_creation: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    config = relationship("Config")
