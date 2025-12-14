#Event models.py
from sqlalchemy import String, DateTime, func, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
import enum

class Base(DeclarativeBase):
    pass

class Event(Base):
    """
    SQLAlchemy model for 'events' table in PostgreSQL database
    """
    __tablename__ = "events"

    event_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    title: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    category_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.category_id"),
        nullable=False
    )

    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    venue: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    banner_url: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    created_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    category = relationship("EventCategory", back_populates="events")
    sessions = relationship("EventSession", back_populates="event")
    registrations = relationship("EventRegistration", back_populates="event")
    organisers = relationship("EventOrganiser", back_populates="event")




class EventCategory(Base):
    __tablename__ = "event_categories"

    category_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    # relationships
    events = relationship(
        "Event",
        back_populates="category",
        cascade="all, delete-orphan"
    )


class OrganiserRole(enum.Enum):
    admin = "admin"
    staff = "staff"
    volunteer = "volunteer"



class EventOrganiser(Base):
    __tablename__ = "event_organisers"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    event_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False
    )

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    role: Mapped[OrganiserRole] = mapped_column(
        Enum(OrganiserRole, name="organiser_role_enum"),
        nullable=False
    )

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # relationships
    event = relationship("Event", back_populates="organisers")
    user = relationship("User", back_populates="organised_events")


class EventSession(Base):
    __tablename__ = "event_sessions"

    session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    event_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    speaker: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # relationships
    event = relationship("Event", back_populates="sessions")


class RegistrationStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    registration_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    event_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False
    )

    user_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True  # guest registration
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    qr_code: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, name="registration_status_enum"),
        default=RegistrationStatus.pending,
        nullable=False
    )

    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # relationships
    event = relationship("Event", back_populates="registrations")
    user = relationship("User", back_populates="event_registrations")
    checkins = relationship(
        "CheckIn",
        back_populates="registration",
        cascade="all, delete-orphan"
    )



class CheckIn(Base):
    __tablename__ = "checkins"

    checkin_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    registration_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("event_registrations.registration_id", ondelete="CASCADE"),
        nullable=False
    )

    checkin_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    gate: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    device_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # relationships
    registration = relationship("EventRegistration", back_populates="checkins")
