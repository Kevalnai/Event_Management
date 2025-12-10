from pydantic import BaseModel, EmailStr
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

# --- 1. Base Schema (Shared Fields) ---
class UserBase(BaseModel):
    """
    Schema for common user fields (used as a base for other schemas).
    """
    username: str
    email: EmailStr
    role: str

# --- 2. Input Schemas (Data from Client to API) ---

class UserRegister(UserBase):
    """
    Schema for user registration (Requires plain password).
    """
    password: str # Plain text password for hashing

class UserLogin(BaseModel):
    """
    Schema for user login (Only needs identifying credential and password).
    """
    username_or_email: str
    password: str 

class UserUpdate(BaseModel):
    """
    Schema for updating user information (All fields are optional).
    """
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    # No password field here, use a dedicated endpoint for password change.

# --- 3. Output Schema (Data from API to Client) ---

class UserResponse(UserBase):
    """
    Schema for sending user data back to the client (NO password field).
    """
    user_id: UUID
    created_at: datetime

    class Config:
        # Crucial for SQLAlchemy: allows Pydantic to read data from the ORM model's attributes.
        from_attributes = True
        # Setting a simple example_dict for documentation
        json_schema_extra = {
            "example": {
                "user_id": str(UUID('12345678-1234-5678-1234-567812345678')),
                "username": "event_manager",
                "email": "manager@events.com",
                "role": "manager",
                "created_at": "2025-11-26T17:23:09.000000+00:00"
            }
        }


class RefreshTokenRequest(BaseModel):
    refresh_token: str

class Token(BaseModel):
    """Schema for returning the access token after successful login."""
    access_token: str
    token_type: str = "bearer"
    refresh_token: str

class TokenData(BaseModel):
    """Schema for the token payload (what's inside the JWT)."""
    user_id: Optional[str] = None