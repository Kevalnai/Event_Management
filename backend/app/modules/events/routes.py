# Routes.py
# Handles HTTP only
# Converts errors to HTTP responses
# Uses FastAPI dependencies

from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ..users.auth import get_current_user

from .schema import EventCreate, EventRead, EventDetail
from .schema import EventCategoryCreate, EventCategoryRead
from .schema import EventSessionCreate, EventSessionRead
from .schema import EventRegistrationCreate, EventRegistrationRead, MyRegistrationRead
from .schema import CheckInCreate, CheckInRead
from .schema import EventOrganiserAdd, EventOrganiserRead, MyOrganiserRoleRead

from .services import (
    EventService,
    EventCategoryService,
    EventSessionService,
    CheckInService
)

router = APIRouter(prefix="/events", tags=["Events Management"])


# =========================================================
# EVENT CATEGORY ROUTES
# =========================================================

@router.post(
    "/categories",
    response_model=EventCategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an event category"
)
def create_category(
    payload: EventCategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Create an event category (or return the existing one with the same name).

    Needed before creating an event, since every event requires a category_id.
    """
    return EventCategoryService.create_category(db, payload)


@router.get(
    "/categories",
    response_model=list[EventCategoryRead],
    summary="List event categories"
)
def list_categories(db: Session = Depends(get_db)):
    return EventCategoryService.list_categories(db)


# =========================================================
# "MY REGISTRATIONS" (must be registered before /{event_id})
# =========================================================

@router.get(
    "/me/registrations",
    response_model=list[MyRegistrationRead],
    summary="List the current user's own registrations/tickets"
)
def my_registrations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    return EventService.list_my_registrations(db, current_user.user_id, limit=limit, offset=offset)


# =========================================================
# EVENT ROUTES
# =========================================================

@router.get(
    "/",
    response_model=list[EventRead],
    summary="List all events"
)
def list_events(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get all events, soonest first.

    - Public endpoint
    - No authentication required
    """
    return EventService.list_events(db, limit=limit, offset=offset)


@router.get(
    "/{event_id}",
    response_model=EventDetail,
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
    response_model=EventRead,
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
    - Creator automatically becomes the event's admin organiser
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
    response_model=EventRegistrationRead,
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


# =========================================================
# EVENT ORGANISER ROUTES
# =========================================================

@router.get(
    "/{event_id}/my-role",
    response_model=MyOrganiserRoleRead,
    summary="Get the current user's organiser role on this event, if any"
)
def get_my_role(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Lets the frontend decide whether to show event-management UI.

    This is a UI-visibility hint only, not a security boundary - every
    actual management endpoint (delete, registrations, organisers,
    check-ins) re-checks RBAC independently regardless of this response.
    """
    role = EventService.get_my_role(db, event_id, current_user.user_id)
    return MyOrganiserRoleRead(role=role)


@router.post(
    "/{event_id}/organisers",
    response_model=EventOrganiserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Grant an organiser role on an event (Admin only)"
)
def add_organiser(
    event_id: UUID,
    payload: EventOrganiserAdd,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Grant (or change) an admin/staff/volunteer role for a user on this event.

    RBAC:
    - Only an existing admin organiser of the event can call this.
    """
    return EventService.add_organiser(
        db=db,
        event_id=event_id,
        actor_user_id=current_user.user_id,
        payload=payload
    )


@router.get(
    "/{event_id}/organisers",
    response_model=list[EventOrganiserRead],
    summary="List organisers for an event (Admin/Staff)"
)
def list_organisers(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return EventService.list_organisers(
        db=db,
        event_id=event_id,
        user_id=current_user.user_id
    )


# =========================================================
# EVENT SESSION ROUTES
# =========================================================

@router.post(
    "/events/{event_id}/sessions",
    response_model=EventSessionRead,
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
    response_model=CheckInRead,
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
    response_model=list[EventRegistrationRead],
    summary="List event registrations (Admin/Staff)"
)
def list_registrations(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
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
        user_id=current_user.user_id,
        limit=limit,
        offset=offset
    )
