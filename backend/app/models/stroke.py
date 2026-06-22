from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StrokeEntry(Base):
    __tablename__ = "strokes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    points: Mapped[str] = mapped_column(String, nullable=False)  # JSON text
    pen_color: Mapped[str] = mapped_column(String, nullable=False, default="#1a1a1a")
    pen_width: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    session: Mapped["WritingSession"] = relationship(
        "WritingSession", back_populates="strokes"
    )
