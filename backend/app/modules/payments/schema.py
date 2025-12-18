from pydantic import BaseModel
from uuid import UUID
from enum import Enum

class PaymentStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class PaymentCreate(BaseModel):
    registration_id: UUID
    amount: float
    currency: str = "USD"

class PaymentRead(BaseModel):
    payment_id: UUID
    registration_id: UUID
    amount: float
    currency: str
    status: PaymentStatus
    transaction_id: str | None

    class Config:
        from_attributes = True
