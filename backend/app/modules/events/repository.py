# repository.py
# it contails ONLY database operations
# NO FastAPI, NO schemas, NO business rules
from sqlalchemy.orm import Session
from uuid import UUID

from .models import (
    Event,
    EventCategory,
    EventOrganiser,
    EventSession,
    EventRegistration,
    CheckIn
)


# -------------------- CATEGORY --------------------

class EventCategoryRepository:

    @staticmethod
    def get_all(db: Session) -> list[EventCategory]:
        return db.query(EventCategory).all()

    @staticmethod
    def get_by_id(db: Session, category_id) -> EventCategory | None:
        return db.query(EventCategory).filter(EventCategory.category_id == category_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> EventCategory | None:
        return db.query(EventCategory).filter(EventCategory.name == name).first()

    @staticmethod
    def create(db: Session, category: EventCategory) -> EventCategory:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category


# -------------------- EVENT --------------------

class EventRepository:

    @staticmethod
    def get_all(db: Session):
        return db.query(Event).all()
    
    @staticmethod
    def get_by_id(db: Session, event_id: UUID) -> Event | None:
        return db.query(Event).filter(Event.event_id == event_id).first()

    @staticmethod
    def create(db: Session, event: Event) -> Event:
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def delete(db: Session, event: Event):
        db.delete(event)
        db.commit()


# -------------------- ORGANISER --------------------

class EventOrganiserRepository:

    @staticmethod
    def get_user_role(
        db: Session,
        user_id: UUID,
        event_id: UUID
    ) -> EventOrganiser | None:
        return (
            db.query(EventOrganiser)
            .filter(
                EventOrganiser.user_id == user_id,
                EventOrganiser.event_id == event_id
            )
            .first()
        )

    @staticmethod
    def create(db: Session, organiser: EventOrganiser) -> EventOrganiser:
        db.add(organiser)
        db.commit()
        db.refresh(organiser)
        return organiser

    @staticmethod
    def get_by_event(db: Session, event_id: UUID) -> list[EventOrganiser]:
        return (
            db.query(EventOrganiser)
            .filter(EventOrganiser.event_id == event_id)
            .all()
        )


# -------------------- SESSION --------------------

class EventSessionRepository:

    @staticmethod
    def create(db: Session, session: EventSession) -> EventSession:
        db.add(session)
        db.commit()
        db.refresh(session)
        return session


# -------------------- REGISTRATION --------------------

class EventRegistrationRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        registration_id: UUID
    ) -> EventRegistration | None:
        return (
            db.query(EventRegistration)
            .filter(EventRegistration.registration_id == registration_id)
            .first()
        )

    @staticmethod
    def create(db: Session, registration: EventRegistration) -> EventRegistration:
        db.add(registration)
        db.commit()
        db.refresh(registration)
        return registration
    
    @staticmethod
    def get_by_user(
        db: Session,
        user_id: UUID
    ) -> list[EventRegistration]:
        return (
            db.query(EventRegistration)
            .filter(EventRegistration.user_id == user_id)
            .order_by(EventRegistration.registered_at.desc())
            .all()
        )

    @staticmethod
    def get_by_event(
        db: Session,
        event_id: UUID
    ) -> list[EventRegistration]:
        return (
            db.query(EventRegistration)
            .filter(EventRegistration.event_id == event_id)
            .order_by(EventRegistration.registered_at.desc())
            .all()
        )

# -------------------- CHECK-IN --------------------

class CheckInRepository:

    @staticmethod
    def create(db: Session, checkin: CheckIn) -> CheckIn:
        db.add(checkin)
        db.commit()
        db.refresh(checkin)
        return checkin