from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from enum import Enum

from ..tickets.schema import TicketRead


def _validate_banner_url(value: str | None) -> str | None:
    """Only accept real http(s) URLs - mirrors the frontend's isImageUrl
    check, as defense in depth for any API client that bypasses it."""
    if value is None:
        return value
    from urllib.parse import urlparse

    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("banner_url must be a valid http:// or https:// URL")
    return value


 


# ======================================================
# Base Schema
# ======================================================

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,   # ORM compatibility
        populate_by_name=True
    )


# ======================================================
# Enums
# ======================================================

class OrganiserRole(str, Enum):
    admin = "admin"
    staff = "staff"
    volunteer = "volunteer"


class RegistrationStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


# ======================================================
# Event Category Schemas
# ======================================================

class EventCategoryBase(BaseSchema):
    name: str
    description: str | None = None


class EventCategoryCreate(EventCategoryBase):
    pass


class EventCategoryRead(EventCategoryBase):
    category_id: UUID


# ======================================================
# Event Session Schemas
# ======================================================

class EventSessionBase(BaseSchema):
    title: str
    speaker: str
    start_time: datetime
    end_time: datetime
    description: str | None = None


class EventSessionCreate(EventSessionBase):
    pass


class EventSessionRead(EventSessionBase):
    session_id: UUID
    event_id: UUID


# ======================================================
# Event Organiser Schemas
# ======================================================

class EventOrganiserBase(BaseSchema):
    event_id: UUID
    user_id: UUID
    role: OrganiserRole


class EventOrganiserCreate(EventOrganiserBase):
    pass


class EventOrganiserAdd(BaseSchema):
    """Grant a role by user_id, or by email when the caller only knows the
    person's email (the normal case from the UI). Exactly one must be set."""
    user_id: UUID | None = None
    email: EmailStr | None = None
    role: OrganiserRole

    @model_validator(mode="after")
    def _require_one_identifier(self):
        if not self.user_id and not self.email:
            raise ValueError("Provide either user_id or email")
        return self


class OrganiserUserSummary(BaseSchema):
    """Just enough to identify who an organiser is in the manage-event UI -
    deliberately not the full UserResponse (no role, no created_at)."""
    user_id: UUID
    username: str
    email: EmailStr


class EventOrganiserRead(EventOrganiserBase):
    id: UUID
    added_at: datetime
    user: OrganiserUserSummary


class MyOrganisedEventRead(BaseSchema):
    """One event this user organises, with their role on it - powers the
    'My events' tab so a host can find events they don't hold a link to."""
    role: OrganiserRole
    added_at: datetime
    event: EventRead


class MyOrganiserRoleRead(BaseSchema):
    """The caller's own organiser role on this event, or null if they have
    none. Purely a UI-visibility hint - every actual management endpoint
    re-checks RBAC independently, so this response carries no privileges."""
    role: OrganiserRole | None = None


# ======================================================
# Check-in Schemas
# ======================================================

class CheckInBase(BaseSchema):
    gate: str | None = None
    device_id: str | None = None


class CheckInCreate(CheckInBase):
    pass


class CheckInRead(CheckInBase):
    checkin_id: UUID
    registration_id: UUID
    checkin_time: datetime


# ======================================================
# Event Registration Schemas
# ======================================================

class EventRegistrationBase(BaseSchema):
    name: str
    email: EmailStr
    phone: str
    

class EventRegistrationCreate(EventRegistrationBase):
    pass


class EventRegistrationRead(EventRegistrationBase):
    registration_id: UUID
    event_id: UUID
    user_id: UUID | None
    qr_code: str
    status: RegistrationStatus
    registered_at: datetime


# ======================================================
# Event Schemas (Main)
# ======================================================

class EventBase(BaseSchema):
    title: str
    description: str | None = None
    category_id: UUID
    start_date: datetime
    end_date: datetime
    venue: str
    address: str
    banner_url: str | None = None
    price: float = 0
    currency: str = "USD"

    _validate_banner_url = field_validator("banner_url")(_validate_banner_url)

    @field_validator("price")
    @classmethod
    def price_cannot_be_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("price cannot be negative")
        return value


class EventCreate(EventBase):
    pass


class EventUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    category_id: UUID | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    venue: str | None = None
    address: str | None = None
    banner_url: str | None = None
    price: float | None = None
    currency: str | None = None

    _validate_banner_url = field_validator("banner_url")(_validate_banner_url)

    @field_validator("price")
    @classmethod
    def price_cannot_be_negative(cls, value: float | None) -> float | None:
        if value is not None and value < 0:
            raise ValueError("price cannot be negative")
        return value


class EventRead(EventBase):
    event_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class EventDetail(EventRead):
    """
    Public event detail. Deliberately excludes `registrations` and
    `organisers` - those carry attendee PII / internal role assignments and
    are only served through the RBAC-gated endpoints
    (GET /events/{id}/registrations, GET /events/{id}/organisers).
    """
    category: EventCategoryRead
    sessions: list[EventSessionRead] = []


# ======================================================
# "My registrations" (dashboard) schema
# ======================================================

class MyRegistrationRead(BaseSchema):
    """A registration plus the event/ticket context a dashboard needs, so
    the frontend doesn't have to make one request per registration."""
    registration_id: UUID
    status: RegistrationStatus
    registered_at: datetime
    qr_code: str
    event: EventRead
    ticket: TicketRead | None = None
