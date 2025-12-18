# Routes.py
# Handles HTTP only
# Converts errors to HTTP responses
# Uses FastAPI dependencies

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...core.databse import get_db
from ..users.auth import get_current_user

from .schema import EventCreate
from .schema import EventSessionCreate
from .schema import CheckInCreate

from .services import (
    EventService,
    EventSessionService,
    CheckInService
)

router = APIRouter(prefix="/events", tags=["Events Management"])


# =========================================================
# EVENT ROUTES
# =========================================================

@router.get(
    "/",
    summary="List all events"
)
def list_events(
    db: Session = Depends(get_db)
):
    """
    Get all events.

    - Public endpoint
    - No authentication required
    """
    return EventService.list_events(db)


@router.get(
    "/{event_id}",
    summary="Get event details"
)
def get_event(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a single event by ID.

    - Public endpoint
    """
    return EventService.get_event(db, event_id)


@router.post(
    "/events",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event"
)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Create a new event.

    - Any authenticated user can create an event
    - Creator becomes the event admin (handled in service later if needed)
    """
    return EventService.create_event(
        db=db,
        payload=payload,
        user_id=current_user.user_id
    )


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an event (Admin only)"
)
def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Delete an event.

    RBAC:
    - Only EVENT ADMIN can delete the event
    """
    EventService.delete_event(
        db=db,
        event_id=event_id,
        user_id=current_user.user_id
    )


@router.post(
    "/{event_id}/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register for an event (authenticated user)"
)
def register_for_event(
    event_id: UUID,
    payload: EventRegistrationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Register the current logged-in user for an event.
    """
    return EventService.register_user(
        db=db,
        event_id=event_id,
        user_id=current_user.user_id,
        payload=payload
    )


@router.post(
    "/{event_id}/register/guest",
    status_code=status.HTTP_201_CREATED,
    summary="Register for an event (guest)"
)
def register_guest(
    event_id: UUID,
    payload: GuestRegistrationCreate,
    db: Session = Depends(get_db)
):
    """
    Register a guest user for an event.

    - No authentication required
    """
    return EventService.register_guest(
        db=db,
        event_id=event_id,
        payload=payload
    )

# =========================================================
# EVENT SESSION ROUTES
# =========================================================

@router.post(
    "/events/{event_id}/sessions",
    status_code=status.HTTP_201_CREATED,
    summary="Create event session (Admin/Staff)"
)
def create_event_session(
    event_id: UUID,
    payload: EventSessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Create a session for an event.

    RBAC:
    - Admin ✅
    - Staff ✅
    - Volunteer ❌
    """
    return EventSessionService.create_session(
        db=db,
        event_id=event_id,
        payload=payload,
        user_id=current_user.user_id
    )



# =========================================================
# CHECK-IN ROUTES
# =========================================================

@router.post(
    "/events/{event_id}/checkins/{registration_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Check-in attendee (Admin/Staff/Volunteer)"
)
def check_in_attendee(
    event_id: UUID,
    registration_id: UUID,
    payload: CheckInCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Check-in an attendee using QR or registration ID.

    RBAC:
    - Admin ✅
    - Staff ✅
    - Volunteer ✅
    """
    return CheckInService.create_checkin(
        db=db,
        event_id=event_id,
        registration_id=registration_id,
        payload=payload,
        user_id=current_user.user_id
    )


@router.get(
    "/{event_id}/registrations",
    summary="List event registrations (Admin/Staff)"
)
def list_registrations(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get all registrations for an event.

    RBAC:
    - Admin ✅
    - Staff ✅
    - Volunteer ❌
    """
    return EventService.list_registrations(
        db=db,
        event_id=event_id,
        user_id=current_user.user_id
    )
