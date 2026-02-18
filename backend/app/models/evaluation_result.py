import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    __table_args__ = (
        Index("ix_eval_config_created", "config_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    config_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("configs.id", ondelete="CASCADE"))
    eval_type: Mapped[str] = mapped_column(String(20))
    results: Mapped[dict] = mapped_column(JSONB)
    confusion_matrix: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    accuracy_per_axis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    overall_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommendations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    config: Mapped["Config"] = relationship(back_populates="evaluation_results")
