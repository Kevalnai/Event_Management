# # Services.py
#  Uses schemas + repository
#  Handles validation & rules
#  NO FastAPI decorators

from uuid import UUID, uuid4
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .models import (
    Event,
    EventCategory,
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
from .schema import EventCreate, EventRegistrationCreate
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
    def get_or_create_category(db: Session, category_id: str | None, name: str = "Default") -> EventCategory:
        """
        Fetch an existing category by ID or create it if it doesn't exist.
        """
        category = None
        if category_id:
            category = db.get(EventCategory, category_id)
        
        if not category:
            category = EventCategory(
                category_id=category_id or uuid4(),
                name=name
            )
            db.add(category)
            db.commit()
            db.refresh(category)
        return category
    
    @staticmethod
    def create_event(
        db: Session,
        payload: EventCreate,
        user_id: UUID
    ) -> Event:
        
        category = EventService.get_or_create_category(
            db,
            payload.category_id,
            #payload.category_name or "Default"
        )   

        event = Event(
            **payload.model_dump(),
            created_by=user_id
        )
        return EventRepository.create(db, event)

    @staticmethod
    def list_events(db: Session) -> list[Event]:
        return EventRepository.get_all(db)

    @staticmethod
    def get_event(db: Session, event_id: UUID) -> Event:
        event = EventRepository.get_by_id(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        return event
    
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

    @staticmethod
    def register_user(
        db: Session,
        event_id: UUID,
        payload: EventRegistrationCreate
    ) -> EventRegistration:
        event = EventRepository.get_by_id(db, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        registration = EventRegistration(
            event_id=event_id,
            user_id=payload.user_id,
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            qr_code=str(uuid4())
        )

        return EventRegistrationRepository.create(db, registration)


    @staticmethod
    def list_registrations(
        db: Session,
        event_id: UUID,
        user_id: UUID
    ) -> list[EventRegistration]:
        """
        List all registrations for an event.
        Only organisers/staff can view registrations.
        """

        RBACService.require_roles(
            db=db,
            user_id=user_id,
            event_id=event_id,
            allowed_roles=[
                OrganiserRole.admin,
                OrganiserRole.staff
            ]
        )

        return EventRegistrationRepository.get_by_event(
            db=db,
            event_id=event_id
        )


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