# from passlib.context import CryptContext

# # Define the password hashing context
# # Schemes: Defines the hashing algorithm to use (bcrypt is standard and secure)
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# def hash_password(password: str) -> str:
#     """Hashes a plain-text password."""
#     return pwd_context.hash(password)

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verifies a plain-text password against a hashed one."""
#     return pwd_context.verify(plain_password, hashed_password)


from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import secrets
from typing import Tuple
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

#PASSWORD HASHING (argon2)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a plaintext password using argon2."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    to_encode = {"sub": subject}
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
# raises jose.JWTError on invalid/expired token
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def create_refresh_token() -> Tuple[str, datetime]:
    """
    Create a secure opaque refresh token (random string).
    Return (token_str, expires_at)
    """
    token = secrets.token_urlsafe(64)
    expires_at = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return token, expires_at