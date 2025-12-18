from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4

class Base(DeclarativeBase):
    pass

class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    registration_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("event_registrations.registration_id", ondelete="CASCADE"),
        nullable=False
    )
    qr_code: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=datetime.utcnow)
    pdf_url: Mapped[str | None] = mapped_column(String(255), nullable=True)  # optional

    # relationships
    registration = relationship("EventRegistration", back_populates="ticket")
