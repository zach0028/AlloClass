import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LearnedRule(Base):
    __tablename__ = "learned_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("configs.id", ondelete="CASCADE"), nullable=False
    )
    axis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("axes.id", ondelete="SET NULL"), nullable=True
    )
    rule_text: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    source_feedback_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    validated_by_user: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    config = relationship("Config", back_populates="learned_rules")
    axis = relationship("Axis")
