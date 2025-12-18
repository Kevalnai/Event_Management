from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class TicketCreate(BaseModel):
    registration_id: UUID

class TicketRead(BaseModel):
    ticket_id: UUID
    registration_id: UUID
    qr_code: str
    issued_at: datetime
    pdf_url: str | None

    class Config:
        orm_mode = True
