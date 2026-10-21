import os
import stripe

from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException

from .models import PaymentStatus
from .repository import PaymentRepository
from ..events.models import EventRegistration


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class PaymentService:

    @staticmethod
    def initiate_payment(
        db: Session,
        registration_id: UUID,
        user_id: UUID | None
    ):
        registration = (
            db.query(EventRegistration)
            .filter(EventRegistration.registration_id == registration_id)
            .first()
        )

        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")

        if registration.user_id and registration.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to pay for this registration"
            )

        event = registration.event
        if not event:
            raise HTTPException(status_code=404, detail="Event not found for this registration")

        # Amount is always derived from the event's price, never from the client.
        amount = event.price
        currency = event.currency

        if amount <= 0:
            raise HTTPException(status_code=400, detail="This event is free - no payment required")

        # Reuse an existing pending PaymentIntent instead of creating a duplicate.
        existing_payment = PaymentRepository.get_pending_by_registration(db, registration_id)
        if existing_payment and existing_payment.stripe_payment_intent_id:
            try:
                intent = stripe.PaymentIntent.retrieve(existing_payment.stripe_payment_intent_id)
            except stripe.error.StripeError as e:
                raise HTTPException(status_code=502, detail=f"Stripe error: {str(e)}")

            if intent.status != "canceled":
                return {
                    "payment": existing_payment,
                    "client_secret": intent.client_secret
                }

        # Stripe expects amount in smallest currency unit.
        # Example: $25.00 -> 2500 cents
        stripe_amount = int(round(amount * 100))

        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=stripe_amount,
                currency=currency.lower(),
                metadata={
                    "registration_id": str(registration_id)
                },
                idempotency_key=f"registration-{registration_id}-init",
                # The frontend confirms with redirect="if_required" and never
                # supplies a return_url (it's a single-page checkout, nothing
                # to redirect back to). Without this, Stripe rejects the
                # confirm call for any account with a redirect-capable method
                # (e.g. Link) enabled in the Dashboard, which is the default -
                # every real card payment would fail at the final step.
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            )
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=502, detail=f"Stripe error: {str(e)}")

        try:
            payment = PaymentRepository.create_payment(
                db=db,
                registration_id=registration_id,
                amount=amount,
                currency=currency,
                stripe_payment_intent_id=payment_intent.id,
                payment_provider="stripe"
            )
        except IntegrityError:
            # Two concurrent calls for the same registration (a double
            # click, a retried request, React StrictMode's double effect in
            # dev) can both pass the "no existing pending payment" check
            # above before either commits, then both get the same Stripe
            # PaymentIntent back via the idempotency key - the second
            # insert here hits the unique constraint on
            # stripe_payment_intent_id. Rather than crash, fall back to the
            # row the other request just created; it's the same PaymentIntent.
            db.rollback()
            payment = PaymentRepository.get_by_stripe_payment_intent(db, payment_intent.id)
            if not payment:
                raise

        return {
            "payment": payment,
            "client_secret": payment_intent.client_secret
        }

    @staticmethod
    def handle_payment_success(
        db: Session,
        payment_intent
    ):  

        stripe_payment_intent_id = payment_intent["id"]

        payment = PaymentRepository.get_by_stripe_payment_intent(
            db,
            stripe_payment_intent_id
        )

        if not payment:
            return None

        # Prevent duplicate webhook processing
        if payment.status == PaymentStatus.completed:
            return payment

        payment.status = PaymentStatus.completed

        registration = (
            db.query(EventRegistration)
            .filter(
                EventRegistration.registration_id
                == payment.registration_id
            )
            .first()
        )

        if registration:
            registration.status = "confirmed"

        db.commit()
        db.refresh(payment)

        return payment

    @staticmethod
    def handle_payment_failure(
        db: Session,
        payment_intent
    ):

        stripe_payment_intent_id = payment_intent["id"]

        payment = PaymentRepository.get_by_stripe_payment_intent(
            db,
            stripe_payment_intent_id
        )

        if not payment:
            return None

        payment.status = PaymentStatus.failed

        db.commit()
        db.refresh(payment)

        return payment