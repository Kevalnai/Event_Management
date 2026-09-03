from sqlalchemy.orm import Session
from uuid import UUID

from .models import Payment, PaymentStatus


class PaymentRepository:

    @staticmethod
    def create_payment(
        db: Session,
        registration_id: UUID,
        amount: float,
        currency: str,
        stripe_payment_intent_id: str | None = None,
        payment_provider: str = "stripe"
    ):
        payment = Payment(
            registration_id=registration_id,
            amount=amount,
            currency=currency,
            stripe_payment_intent_id=stripe_payment_intent_id,
            payment_provider=payment_provider,
            status=PaymentStatus.pending
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return payment

    @staticmethod
    def get_by_id(
        db: Session,
        payment_id: UUID
    ):
        return (
            db.query(Payment)
            .filter(Payment.payment_id == payment_id)
            .first()
        )

    @staticmethod
    def get_pending_by_registration(
        db: Session,
        registration_id: UUID
    ):
        return (
            db.query(Payment)
            .filter(
                Payment.registration_id == registration_id,
                Payment.status == PaymentStatus.pending
            )
            .order_by(Payment.created_at.desc())
            .first()
        )

    @staticmethod
    def get_by_stripe_payment_intent(
        db: Session,
        stripe_payment_intent_id: str
    ):
        return (
            db.query(Payment)
            .filter(
                Payment.stripe_payment_intent_id
                == stripe_payment_intent_id
            )
            .first()
        )

    @staticmethod
    def update_payment_status(
        db: Session,
        payment_id: UUID,
        status: PaymentStatus
    ):
        payment = (
            db.query(Payment)
            .filter(Payment.payment_id == payment_id)
            .first()
        )

        if payment:
            payment.status = status
            db.commit()
            db.refresh(payment)

        return payment
