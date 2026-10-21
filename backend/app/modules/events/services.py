# # Services.py
#  Uses schemas + repository
#  Handles validation & rules
#  NO FastAPI decorators

from uuid import UUID, uuid4
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import (
    Event,
    EventCategory,
    EventOrganiser,
    EventSession,
    EventRegistration,
    CheckIn,
    OrganiserRole,
    RegistrationStatus
)
from .repository import (
    EventRepository,
    EventCategoryRepository,
    EventOrganiserRepository,
    EventSessionRepository,
    EventRegistrationRepository,
    CheckInRepository
)
from .schema import EventCreate, EventRegistrationCreate, EventOrganiserAdd
from .schema import EventSessionCreate, EventCategoryCreate
from .schema import CheckInCreate
from ..users.repository import get_user_by_email


# -------------------- CATEGORY SERVICE --------------------

class EventCategoryService:

    @staticmethod
    def create_category(db: Session, payload: EventCategoryCreate) -> EventCategory:
        existing = EventCategoryRepository.get_by_name(db, payload.name)
        if existing:
            return existing
        category = EventCategory(**payload.model_dump())
        return EventCategoryRepository.create(db, category)

    @staticmethod
    def list_categories(db: Session) -> list[EventCategory]:
        return EventCategoryRepository.get_all(db)


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
        try:
            event = EventRepository.create(db, event)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An event with this title already exists"
            )

        # The creator is automatically the event's admin organiser,
        # otherwise no one could ever pass the RBAC checks below.
        EventOrganiserRepository.create(
            db,
            EventOrganiser(
                event_id=event.event_id,
                user_id=user_id,
                role=OrganiserRole.admin
            )
        )

        return event

    @staticmethod
    def list_events(db: Session, limit: int = 50, offset: int = 0) -> list[Event]:
        return EventRepository.get_all(db, limit=limit, offset=offset)

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
        user_id: UUID,
        payload: EventRegistrationCreate
    ) -> EventRegistration:
        event = EventRepository.get_by_id(db, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        registration = EventRegistration(
            event_id=event_id,
            user_id=user_id,
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            qr_code=str(uuid4()),
            # Free events skip the payment step entirely - Stripe won't even
            # accept a $0 PaymentIntent, so there's nothing to pay for.
            status=RegistrationStatus.confirmed if event.price <= 0 else RegistrationStatus.pending
        )

        return EventRegistrationRepository.create(db, registration)


    @staticmethod
    def add_organiser(
        db: Session,
        event_id: UUID,
        actor_user_id: UUID,
        payload: EventOrganiserAdd
    ) -> EventOrganiser:
        """
        Grant (or change) an organiser role on an event.
        Only an existing admin organiser of the event may do this.
        """
        RBACService.require_roles(
            db,
            actor_user_id,
            event_id,
            allowed_roles=[OrganiserRole.admin]
        )

        if not EventRepository.get_by_id(db, event_id):
            raise HTTPException(status_code=404, detail="Event not found")

        target_user_id = payload.user_id
        if payload.email:
            target_user = get_user_by_email(db, payload.email)
            if not target_user:
                raise HTTPException(
                    status_code=404,
                    detail="No account found with that email"
                )
            target_user_id = target_user.user_id

        existing = EventOrganiserRepository.get_user_role(
            db, target_user_id, event_id
        )
        if existing:
            existing.role = payload.role
            db.commit()
            db.refresh(existing)
            return existing

        return EventOrganiserRepository.create(
            db,
            EventOrganiser(
                event_id=event_id,
                user_id=target_user_id,
                role=payload.role
            )
        )

    @staticmethod
    def list_my_organised_events(db: Session, user_id: UUID) -> list[EventOrganiser]:
        """Every event the current user organises, any role - powers the
        'My events' tab so a host isn't limited to bookmarking event URLs."""
        return EventOrganiserRepository.get_by_user(db, user_id)

    @staticmethod
    def get_my_role(
        db: Session,
        event_id: UUID,
        user_id: UUID
    ) -> OrganiserRole | None:
        """The caller's own organiser role on this event, or None. Used only
        to drive frontend UI - never treated as a security decision itself."""
        organiser = EventOrganiserRepository.get_user_role(db, user_id, event_id)
        return organiser.role if organiser else None

    @staticmethod
    def list_organisers(
        db: Session,
        event_id: UUID,
        user_id: UUID
    ) -> list[EventOrganiser]:
        RBACService.require_roles(
            db,
            user_id,
            event_id,
            allowed_roles=[OrganiserRole.admin, OrganiserRole.staff]
        )
        return EventOrganiserRepository.get_by_event(db, event_id)

    @staticmethod
    def list_registrations(
        db: Session,
        event_id: UUID,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
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
            event_id=event_id,
            limit=limit,
            offset=offset
        )

    @staticmethod
    def list_my_registrations(
        db: Session, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[EventRegistration]:
        """All of the current user's own registrations, across every event."""
        return EventRegistrationRepository.get_by_user(db, user_id, limit=limit, offset=offset)


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

        # Keep the 404 generic rather than distinguishing "doesn't exist" from
        # "belongs to a different event" - an organiser of event A has no
        # legitimate reason to learn that a given registration_id belongs to
        # event B, and this also closes the door on checking it in there.
        if not registration or registration.event_id != event_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found"
            )

        if registration.status != RegistrationStatus.confirmed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration is not confirmed - cannot check in"
            )

        if registration.checkins:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already checked in"
            )

        checkin = CheckIn(
            registration_id=registration_id,
            **payload.model_dump()
        )

        return CheckInRepository.create(db, checkin)