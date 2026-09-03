from sqlalchemy.orm import Session
from uuid import UUID

from .models import Ticket


class TicketRepository:

    @staticmethod
    def get_by_registration_id(db: Session, registration_id: UUID) -> Ticket | None:
        return (
            db.query(Ticket)
            .filter(Ticket.registration_id == registration_id)
            .first()
        )

    @staticmethod
    def create(db: Session, ticket: Ticket) -> Ticket:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket
