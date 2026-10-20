import os
import stripe

from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.limiter import limiter
from ..users.auth import get_current_user
from .schema import PaymentCreate, PaymentInitiateResponse
from .services import PaymentService


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


@router.post(
    "/",
    response_model=PaymentInitiateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Stripe PaymentIntent for a registration"
)
@limiter.limit("10/minute")
def initiate_payment(
    request: Request,
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Creates (or reuses) a Stripe PaymentIntent for the given registration
    and returns the client_secret the frontend uses to confirm payment.

    The amount is derived server-side from the event's price - never
    trusted from the client.
    """
    return PaymentService.initiate_payment(
        db=db,
        registration_id=payload.registration_id,
        user_id=current_user.user_id
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):

    payload = await request.body()

    signature = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            STRIPE_WEBHOOK_SECRET
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid payload"
        )

    except stripe.SignatureVerificationError:
        raise HTTPException(
            status_code=400,
            detail="Invalid signature"
        )

    if event["type"] == "payment_intent.succeeded":

        payment_intent = event["data"]["object"]

        PaymentService.handle_payment_success(
            db=db,
            payment_intent=payment_intent
        )

    elif event["type"] == "payment_intent.payment_failed":

        payment_intent = event["data"]["object"]

        PaymentService.handle_payment_failure(
            db=db,
            payment_intent=payment_intent
        )

    return {"received": True}