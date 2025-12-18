# repository.py
# it contails ONLY database operations
# NO FastAPI, NO schemas, NO business rules
from sqlalchemy.orm import Session
from uuid import UUID
from .models import Event


class EventRepository:

    @staticmethod
    def create(db: Session, event: Event) -> Event:
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_by_id(db: Session, event_id: UUID) -> Event | None:
        return db.query(Event).filter(Event.event_id == event_id).first()

    @staticmethod
    def get_all(db: Session) -> list[Event]:
        return db.query(Event).all()

    @staticmethod
    def update(db: Session, event: Event) -> Event:
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def delete(db: Session, event: Event) -> None:
        db.delete(event)
        db.commit()
