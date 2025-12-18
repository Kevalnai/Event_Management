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
