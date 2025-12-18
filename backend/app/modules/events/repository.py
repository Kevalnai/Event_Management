# repository.py
# it contails ONLY database operations
# NO FastAPI, NO schemas, NO business rules
from sqlalchemy.orm import Session
from uuid import UUID
from .models import Event


from uuid import UUID
from sqlalchemy.orm import Session

from .models import (
    Event,
    EventOrganiser,
    EventSession,
    EventRegistration,
    CheckIn
)


# -------------------- EVENT --------------------

class EventRepository:

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


# -------------------- CHECK-IN --------------------

class CheckInRepository:

    @staticmethod
    def create(db: Session, checkin: CheckIn) -> CheckIn:
        db.add(checkin)
        db.commit()
        db.refresh(checkin)
        return checkin