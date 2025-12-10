# py

from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from . import models, schema
from .services import hash_password # Import the hashing utility
from datetime import datetime

# --- Create (Register) User ---
def create_user(db: Session, user: schema.UserRegister):
    """
    Creates a new User record in the database.
    """
    # 1. Hash the incoming plain password
    hashed_pass = hash_password(user.password)
    
    # 2. Create an instance of the SQLAlchemy User Model
    # We use a dictionary unpack here, passing the hash instead of the plain password
    db_user = models.User(
        username=user.username,
        email=user.email,
        role=user.role,
        hashed_password=hashed_pass # Store the hash, not the plain text!
    )
    
    # 3. Add to the session, commit, and refresh to get auto-generated fields (like user_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# --- Read (Get) User by Email (for checking duplicates) ---
def get_user_by_email(db: Session, email: str):
    """
    Retrieves a user by their email address.
    """
    # Use SQLAlchemy 2.0 style select statement
    stmt = select(models.User).where(models.User.email == email)
    return db.execute(stmt).scalars().first()

# --- Read (Get) User by Username (for checking duplicates) ---
def get_user_by_username(db: Session, username: str):
    """
    Retrieves a user by their username.
    """
    stmt = select(models.User).where(models.User.username == username)
    return db.execute(stmt).scalars().first()

def get_user_by_username_or_email(db: Session, identifier: str):
    """
    Retrieves a user by username or email.
    """
    from .models import User  # Import Model locally to avoid circular dependencies
    
    # Check for email first
    stmt = select(User).where(User.email == identifier)
    user = db.execute(stmt).scalars().first()
    
    if user:
        return user
        
    # If not found by email, check for username
    stmt = select(User).where(User.username == identifier)
    user = db.execute(stmt).scalars().first()
    
    return user

def create_user(db: Session, user: schema.UserRegister):
    hashed_pass = hash_password(user.password)
    db_user = models.User(
    username=user.username,
    email=user.email,
    role=user.role,
    hashed_password=hashed_pass
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    stmt = select(models.User).where(models.User.email == email)
    return db.execute(stmt).scalars().first()

def get_user_by_username(db: Session, username: str):
    stmt = select(models.User).where(models.User.username == username)
    return db.execute(stmt).scalars().first()

def get_user_by_username_or_email(db: Session, identifier: str):
    stmt = select(models.User).where(models.User.email == identifier)
    user = db.execute(stmt).scalars().first()
    if user:
        return user

    stmt = select(models.User).where(models.User.username == identifier)
    return db.execute(stmt).scalars().first()

# ----------------- Refresh token helpers -----------------

def save_refresh_token(db: Session, user_id, token_str: str):
    rt = models.RefreshToken(token=token_str, user_id=user_id)
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt

def get_refresh_token(db: Session, token_str: str):
    stmt = select(models.RefreshToken).where(models.RefreshToken.token == token_str)
    return db.execute(stmt).scalars().first()

def revoke_refresh_token(db: Session, token_str: str):
    rt = get_refresh_token(db, token_str)
    if rt:
        rt.revoked = True
        db.add(rt)
        db.commit()
        return rt

def revoke_user_refresh_tokens(db: Session, user_id):
    stmt = select(models.RefreshToken).where(models.RefreshToken.user_id == user_id)
    tokens = db.execute(stmt).scalars().all()
    for t in tokens:
        t.revoked = True
        db.add(t)
        db.commit()

# ----------------- Password reset helpers -----------------

def create_password_reset_token(db: Session, user_id, token_str: str, expires_at: datetime):
    pr = models.PasswordResetToken(token=token_str, user_id=user_id, expires_at=expires_at)
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr

def get_password_reset_token(db: Session, token_str: str):
    stmt = select(models.PasswordResetToken).where(models.PasswordResetToken.token == token_str)
    return db.execute(stmt).scalars().first()

def mark_password_reset_used(db: Session, token_obj):
    token_obj.used = True
    db.add(token_obj)
    db.commit()