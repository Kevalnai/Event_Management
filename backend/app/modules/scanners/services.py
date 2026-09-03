from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.modules.events.models import CheckIn, OrganiserRole
from app.modules.events.services import RBACService
from app.modules.tickets.models import Ticket


class ScannerService:

    @staticmethod
    def scan_qr(
        db: Session,
        qr_code: str,
        user_id: UUID,
        gate: str | None = None,
        device_id: str | None = None
    ) -> CheckIn:
        ticket = db.query(Ticket).filter(Ticket.qr_code == qr_code).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Invalid or unknown ticket QR code")

        registration = ticket.registration
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found for this ticket")

        RBACService.require_roles(
            db,
            user_id,
            registration.event_id,
            allowed_roles=[
                OrganiserRole.admin,
                OrganiserRole.staff,
                OrganiserRole.volunteer
            ]
        )

        if registration.checkins:
            raise HTTPException(status_code=409, detail="Already checked in")

        checkin = CheckIn(
            registration_id=registration.registration_id,
            gate=gate,
            device_id=device_id
        )

        db.add(checkin)
        db.commit()
        db.refresh(checkin)

        return checkin
