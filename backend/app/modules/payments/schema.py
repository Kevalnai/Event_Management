from pydantic import BaseModel
from uuid import UUID
from enum import Enum

class PaymentStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class PaymentCreate(BaseModel):
    registration_id: UUID


class PaymentRead(BaseModel):
    payment_id: UUID
    registration_id: UUID
    amount: float
    currency: str
    status: PaymentStatus
    stripe_payment_intent_id: str | None
    payment_provider: str | None

    class Config:
        from_attributes = True


class PaymentInitiateResponse(BaseModel):
    payment: PaymentRead
    client_secret: str
