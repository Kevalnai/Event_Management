from sqlalchemy.orm import Session
from uuid import UUID


class PaymentRepository:

    @staticmethod
    def create_payment(db, registration_id: UUID, amount: float, currency: str):
        from .models import Payment
        payment = Payment(
            registration_id=registration_id,
            amount=amount,
            currency=currency,
            status="pending"
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def update_payment_status(db, payment_id: UUID, status: str, transaction_id: str):
        from .models import Payment
        payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
        if payment:
            payment.status = status
            payment.transaction_id = transaction_id
            db.commit()
            db.refresh(payment)
        return payment


