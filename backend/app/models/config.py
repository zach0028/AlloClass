import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Config(Base):
    __tablename__ = "configs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    template_source: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    axes: Mapped[list["Axis"]] = relationship(
        back_populates="config", cascade="all, delete-orphan"
    )
    classification_results: Mapped[list["ClassificationResult"]] = relationship(
        back_populates="config"
    )
    evaluation_results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="config"
    )
    learned_rules: Mapped[list["LearnedRule"]] = relationship(
        back_populates="config", cascade="all, delete-orphan"
    )
