from pydantic import BaseModel, ConfigDict
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from enum import Enum


 


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
    event_id: UUID


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


class EventOrganiserRead(EventOrganiserBase):
    id: UUID
    added_at: datetime


# ======================================================
# Check-in Schemas
# ======================================================

class CheckInBase(BaseSchema):
    gate: str | None = None
    device_id: str | None = None


class CheckInCreate(CheckInBase):
    registration_id: UUID


class CheckInRead(CheckInBase):
    checkin_id: UUID
    registration_id: UUID
    checkin_time: datetime


# ======================================================
# Event Registration Schemas
# ======================================================

class EventRegistrationBase(BaseSchema):
    name: str
    email: str
    phone: str


class EventRegistrationCreate(EventRegistrationBase):
    event_id: UUID
    user_id: UUID | None = None  # guest registration support


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


class EventRead(EventBase):
    event_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class EventDetail(EventRead):
    category: EventCategoryRead
    sessions: list[EventSessionRead] = []
    registrations: list[EventRegistrationRead] = []
    organisers: list[EventOrganiserRead] = []
