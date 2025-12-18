# # Services.py
#  Uses schemas + repository
#  Handles validation & rules
#  NO FastAPI decorators

from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .models import (
    Event,
    EventSession,
    EventRegistration,
    CheckIn,
    OrganiserRole
)
from .repository import (
    EventRepository,
    EventOrganiserRepository,
    EventSessionRepository,
    EventRegistrationRepository,
    CheckInRepository
)
from .schema import EventCreate
from .schema import EventSessionCreate
from .schema import CheckInCreate


# -------------------- RBAC CORE --------------------

class RBACService:

    @staticmethod
    def require_roles(
        db: Session,
        user_id: UUID,
        event_id: UUID,
        allowed_roles: list[OrganiserRole]
    ):
        organiser = EventOrganiserRepository.get_user_role(
            db=db,
            user_id=user_id,
            event_id=event_id
        )

        if not organiser or organiser.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )


# -------------------- EVENT SERVICE --------------------

class EventService:

    @staticmethod
    def create_event(
        db: Session,
        payload: EventCreate,
        user_id: UUID
    ) -> Event:
        event = Event(
            **payload.model_dump(),
            created_by=user_id
        )
        return EventRepository.create(db, event)

    @staticmethod
    def delete_event(
        db: Session,
        event_id: UUID,
        user_id: UUID
    ):
        RBACService.require_roles(
            db,
            user_id,
            event_id,
            allowed_roles=[OrganiserRole.admin]
        )

        event = EventRepository.get_by_id(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        EventRepository.delete(db, event)


# -------------------- SESSION SERVICE --------------------

class EventSessionService:

    @staticmethod
    def create_session(
        db: Session,
        event_id: UUID,
        payload: EventSessionCreate,
        user_id: UUID
    ) -> EventSession:
        RBACService.require_roles(
            db,
            user_id,
            event_id,
            allowed_roles=[
                OrganiserRole.admin,
                OrganiserRole.staff
            ]
        )

        session = EventSession(
            event_id=event_id,
            **payload.model_dump()
        )
        return EventSessionRepository.create(db, session)


# -------------------- CHECK-IN SERVICE --------------------

class CheckInService:

    @staticmethod
    def create_checkin(
        db: Session,
        event_id: UUID,
        registration_id: UUID,
        payload: CheckInCreate,
        user_id: UUID
    ) -> CheckIn:
        RBACService.require_roles(
            db,
            user_id,
            event_id,
            allowed_roles=[
                OrganiserRole.admin,
                OrganiserRole.staff,
                OrganiserRole.volunteer
            ]
        )

        registration = EventRegistrationRepository.get_by_id(
            db,
            registration_id
        )

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found"
            )

        checkin = CheckIn(
            registration_id=registration_id,
            **payload.model_dump()
        )

        return CheckInRepository.create(db, checkin)