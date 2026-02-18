import uuid
from datetime import datetime

from sqlalchemy import Float, String, Text, Integer, DateTime, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Axis(Base):
    __tablename__ = "axes"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    config_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("configs.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    challenger_threshold: Mapped[float] = mapped_column(
        Float, default=0.75, server_default=text("0.75")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    config: Mapped["Config"] = relationship(back_populates="axes")
    categories: Mapped[list["AxisCategory"]] = relationship(
        back_populates="axis", cascade="all, delete-orphan"
    )
