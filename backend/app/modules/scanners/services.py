from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.modules.events.models import CheckIn, EventRegistration

class ScannerService:

    @staticmethod
    def check_in(
        db: Session,
        registration_id: UUID,
        gate: str | None = None,
        device_id: str | None = None
    ):
        registration = db.get(EventRegistration, registration_id)

        if not registration:
            raise ValueError("Invalid registration")

        if registration.checkins:
            raise ValueError("Already checked in")

        checkin = CheckIn(
            registration_id=registration_id,
            gate=gate,
            device_id=device_id
        )

        db.add(checkin)
        db.commit()
        db.refresh(checkin)

        return checkin
