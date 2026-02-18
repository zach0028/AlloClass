import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ClassificationResult(Base):
    __tablename__ = "classification_results"
    __table_args__ = (
        Index("ix_classif_config_created", "config_id", "created_at"),
        Index("ix_classif_confidence", "overall_confidence"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    config_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("configs.id", ondelete="CASCADE"))
    input_text: Mapped[str] = mapped_column(Text)
    results: Mapped[dict] = mapped_column(JSONB)
    overall_confidence: Mapped[float] = mapped_column(Float)
    was_challenged: Mapped[bool] = mapped_column(Boolean, default=False)
    challenger_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    model_used: Mapped[str] = mapped_column(String(50))
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    vote_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    embedding = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    config: Mapped["Config"] = relationship(back_populates="classification_results")
    user_feedbacks: Mapped[list["UserFeedback"]] = relationship(
        back_populates="classification_result"
    )
