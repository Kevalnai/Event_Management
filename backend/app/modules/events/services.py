# # Services.py
#  Uses schemas + repository
#  Handles validation & rules
#  NO FastAPI decorators

from uuid import UUID
from sqlalchemy.orm import Session

from .models import Event
from .schema import EventCreate, EventUpdate
from .repository import EventRepository


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
    def get_event(db: Session, event_id: UUID) -> Event:
        event = EventRepository.get_by_id(db, event_id)
        if not event:
            raise ValueError("Event not found")
        return event

    @staticmethod
    def update_event(
        db: Session,
        event_id: UUID,
        payload: EventUpdate
    ) -> Event:

        event = EventRepository.get_by_id(db, event_id)
        if not event:
            raise ValueError("Event not found")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(event, field, value)

        return EventRepository.update(db, event)

    @staticmethod
    def delete_event(db: Session, event_id: UUID) -> None:
        event = EventRepository.get_by_id(db, event_id)
        if not event:
            raise ValueError("Event not found")

        EventRepository.delete(db, event)
