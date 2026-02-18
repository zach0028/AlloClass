import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserFeedback(Base):
    __tablename__ = "user_feedbacks"
    __table_args__ = (
        Index("ix_feedback_classification", "classification_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    classification_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classification_results.id", ondelete="CASCADE")
    )
    axis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("axes.id"))
    corrected_category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("axes_categories.id"), nullable=True
    )
    original_category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("axes_categories.id"), nullable=True
    )
    reasoning_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_type: Mapped[str] = mapped_column(String(20))
    review_status: Mapped[str] = mapped_column(
        String(20), default="corrected", server_default=text("'corrected'")
    )
    active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    classification_result: Mapped["ClassificationResult"] = relationship(
        back_populates="user_feedbacks"
    )
