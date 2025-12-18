from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ...core.databse import get_db
from ..users.auth import get_current_user
from .schema import CheckInCreate
from .services import CheckInService
from ..events.schema import CheckInRead

router = APIRouter(prefix="/scanner", tags=["Scanner"])

@router.post("/scan", response_model=CheckInRead, status_code=status.HTTP_201_CREATED)
def scan_ticket(payload: CheckInCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Scan a ticket QR code to check-in an attendee.

    Roles allowed: Admin / Staff / Volunteer
    """
    return CheckInService.scan_qr(
        db=db,
        qr_code=payload.qr_code,
        gate=payload.gate,
        device_id=payload.device_id
    )
