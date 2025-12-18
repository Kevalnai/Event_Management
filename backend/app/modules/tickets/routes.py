from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from ...core.database import get_db
from ..users.auth import get_current_user
from .services import TicketService
from .schema import TicketRead

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.post("/{registration_id}", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def issue_ticket(registration_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Issue a ticket for a confirmed registration.

    - Only paid registrations can get a ticket
    """
    return TicketService.generate_ticket(db=db, registration_id=str(registration_id))
