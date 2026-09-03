from uuid import UUID, uuid4
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import Ticket
from .repository import TicketRepository
from ..events.models import EventRegistration, RegistrationStatus


class TicketService:

    @staticmethod
    def generate_ticket(db: Session, registration_id: UUID, user_id: UUID | None) -> Ticket:
        registration = db.query(EventRegistration).filter_by(registration_id=registration_id).first()
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")

        if registration.user_id and registration.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to issue a ticket for this registration"
            )

        if registration.status != RegistrationStatus.confirmed:
            raise HTTPException(
                status_code=400,
                detail="Payment not completed. Ticket cannot be issued."
            )

        existing = TicketRepository.get_by_registration_id(db, registration_id)
        if existing:
            return existing

        # Unique QR payload identifying this ticket
        qr_data = f"{registration.registration_id}-{uuid4()}"

        ticket = Ticket(
            registration_id=registration.registration_id,
            qr_code=qr_data,
            pdf_url=None  # optional: later generate PDF & store URL
        )

        return TicketRepository.create(db, ticket)
