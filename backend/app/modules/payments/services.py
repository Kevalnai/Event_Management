from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

class PaymentService:

    @staticmethod
    def initiate_payment(db, registration_id: UUID, amount: float, currency: str = "USD"):
        """
        Create a payment entry with status 'pending'
        """
        from .repository import PaymentRepository
        return PaymentRepository.create_payment(db, registration_id, amount, currency)

    @staticmethod
    def complete_payment(db, payment_id: UUID, transaction_id: str):
        """
        Mark payment as completed and update registration
        """
        from .repository import PaymentRepository
        payment = PaymentRepository.update_payment_status(db, payment_id, "completed", transaction_id)

        # Update the registration status to confirmed
        if payment:
            from .models import EventRegistration
            registration = db.query(EventRegistration).filter(EventRegistration.registration_id == payment.registration_id).first()
            if registration:
                registration.status = "confirmed"
                db.commit()
        return payment

    @staticmethod
    def fail_payment(db, payment_id: UUID, transaction_id: str):
        from .repository import PaymentRepository
        return PaymentRepository.update_payment_status(db, payment_id, "failed", transaction_id)
