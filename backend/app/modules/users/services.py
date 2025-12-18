
# services.py

from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import secrets
from typing import Tuple
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -------------------------------------------------------------------
# CONFIGURATION (with safe fallbacks)
# -------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))


# -------------------------------------------------------------------
# PASSWORD HASHING CONFIG (Argon2)
# -------------------------------------------------------------------
"""
Argon2 provides:
- built-in salting
- memory-hard hashing (resistant to GPU attacks)
- recommended for modern applications
"""
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    """Hash a plaintext password securely using Argon2."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored Argon2 hash."""
    return pwd_context.verify(plain_password, hashed_password)



# -------------------------------------------------------------------
# ACCESS TOKEN CREATION
# -------------------------------------------------------------------
def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.
    Uses 'sub' as the payload field (JWT standard).
    """
    to_encode = {"sub": subject}

    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decodes JWT and returns payload.
    Raises jose.JWTError if invalid or expired.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])



# -------------------------------------------------------------------
# REFRESH TOKEN CREATION
# -------------------------------------------------------------------
def create_refresh_token() -> Tuple[str, datetime]:
    """
    Creates a secure opaque refresh token (random string).
    Refresh tokens are NOT JWTs.
    They are stored in the DB and can be revoked.
    """
    token = secrets.token_urlsafe(64)
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return token, expires_at
