from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class Base(DeclarativeBase):
    pass

class CheckIn(Base):
    __tablename__ = "checkins"

    checkin_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    registration_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("event_registrations.registration_id", ondelete="CASCADE"),
        nullable=False
    )
    checkin_time: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    gate: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # relationships
    registration = relationship("EventRegistration", back_populates="checkins")
