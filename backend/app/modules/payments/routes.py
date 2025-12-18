from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from ...core.databse import get_db
from ..users.auth import get_current_user
from .schema import PaymentCreate, PaymentRead
from .services import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def initiate_payment(payload: PaymentCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Create a payment record for a registration
    """
    return PaymentService.initiate_payment(
        db=db,
        registration_id=payload.registration_id,
        amount=payload.amount,
        currency=payload.currency
    )


@router.post("/{payment_id}/complete", response_model=PaymentRead)
def complete_payment(payment_id: UUID, transaction_id: str, db: Session = Depends(get_db)):
    """
    Mark payment as completed
    """
    return PaymentService.complete_payment(db=db, payment_id=payment_id, transaction_id=transaction_id)


@router.post("/{payment_id}/fail", response_model=PaymentRead)
def fail_payment(payment_id: UUID, transaction_id: str, db: Session = Depends(get_db)):
    """
    Mark payment as failed
    """
    return PaymentService.fail_payment(db=db, payment_id=payment_id, transaction_id=transaction_id)
