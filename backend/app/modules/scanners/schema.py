from pydantic import BaseModel

class CheckInCreate(BaseModel):
    qr_code: str
    gate: str | None = None
    device_id: str | None = None
