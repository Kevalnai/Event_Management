from sqlalchemy import String, Float, Enum, DateTime, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
import enum
from app.core.database import Base




class PaymentStatus(enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    registration_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("event_registrations.registration_id", ondelete="CASCADE"),
        nullable=False
    )

    amount: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"),
        default=PaymentStatus.pending,
        nullable=False
    ) 

    transaction_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationship
    registration = relationship("EventRegistration", back_populates="payments")
