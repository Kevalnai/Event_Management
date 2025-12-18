from sqlalchemy.orm import Session
from ..events.models import  CheckIn
from ..events.models import EventRegistration
from ..tickets.models import Ticket
from uuid import uuid4
from fastapi import HTTPException, status

class CheckInService:

    @staticmethod
    def scan_qr(db: Session, qr_code: str, gate: str | None = None, device_id: str | None = None):
        # Find ticket by QR code
        ticket = db.query(Ticket).filter(Ticket.qr_code == qr_code).first()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid QR code")

        registration = ticket.registration

        # Ensure payment is confirmed
        if registration.status != "confirmed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration not paid")

        # Check if already checked in
        existing_checkin = db.query(CheckIn).filter(CheckIn.registration_id == registration.registration_id).first()
        if existing_checkin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already checked in")

        # Create check-in
        checkin = CheckIn(
            registration_id=registration.registration_id,
            gate=gate,
            device_id=device_id
        )
        db.add(checkin)
        db.commit()
        db.refresh(checkin)

        return checkin
