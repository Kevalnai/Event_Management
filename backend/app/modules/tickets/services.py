import qrcode
import io
from uuid import UUID, uuid4
import base64
from datetime import datetime
from sqlalchemy.orm import Session
from .models import Ticket
from ..events.models import EventRegistration

class TicketService:

    @staticmethod
    def generate_ticket(db: Session, registration_id: str) -> Ticket:
        # Check if registration exists and is paid
        registration = db.query(EventRegistration).filter_by(registration_id=registration_id).first()
        if not registration:
            raise ValueError("Registration not found")
        if registration.status != "confirmed":
            raise ValueError("Payment not completed. Ticket cannot be issued.")

        # Generate unique QR code (could be UUID or hash)
        qr_data = f"{registration.registration_id}-{uuid4()}"
        qr_img = qrcode.make(qr_data)

        # Save QR code as base64 (for API response)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_b64 = base64.b64encode(buffer.getvalue()).decode()

        # Save ticket in DB
        ticket = Ticket(
            registration_id=registration.registration_id,
            qr_code=qr_data,
            pdf_url=None  # optional: later generate PDF & store URL
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        return ticket
