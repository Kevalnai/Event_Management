from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ..users.auth import get_current_user
from .schema import CheckInCreate
from .services import ScannerService
from ..events.schema import CheckInRead

router = APIRouter(prefix="/scanner", tags=["Scanner"])

@router.post("/scan", response_model=CheckInRead, status_code=status.HTTP_201_CREATED)
def scan_ticket(payload: CheckInCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Scan a ticket's QR code to check-in an attendee.

    RBAC: Admin / Staff / Volunteer organiser of the ticket's event.
    """
    return ScannerService.scan_qr(
        db=db,
        qr_code=payload.qr_code,
        user_id=current_user.user_id,
        gate=payload.gate,
        device_id=payload.device_id
    )
