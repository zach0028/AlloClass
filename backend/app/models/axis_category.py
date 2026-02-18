import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AxisCategory(Base):
    __tablename__ = "axes_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    axis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("axes.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    axis: Mapped["Axis"] = relationship(back_populates="categories")
