# auth.py

import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from uuid import UUID
from typing import Dict

from ...core.limiter import limiter
from . import schema, repository
from ...core.database import get_db
from .services import (
    verify_password,
    hash_password,
    create_refresh_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from .models import User
from .schema import RefreshTokenRequest
from . import repository as repo

# JWT config (SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES) lives in
# services.py so there is exactly one source of truth for the signing key.

# FastAPI built-in OAuth2 Bearer token reader
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(prefix="/auth", tags=["Authentication"])


# -------------------------------------------------------------------
# CREATE ACCESS TOKEN
# -------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Creates a JWT access token with an expiration time.
    Uses "sub" field — the standard JWT subject claim.
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# -------------------------------------------------------------------
# DECODE TOKEN & GET CURRENT USER
# -------------------------------------------------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Verifies JWT, extracts "sub" (user ID), fetches user from DB, and returns it.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")  # must match create_access_token field

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token (missing subject)")

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Validate UUID format
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID format")

    # Fetch user
    user = db.get(User, user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """
    Dependency that only lets global admins (User.role == "admin") through.
    Distinct from the per-event OrganiserRole RBAC in the events module.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


# -------------------------------------------------------------------
# REGISTER USER
# -------------------------------------------------------------------
@router.post("/register", response_model=schema.UserResponse)
@limiter.limit("5/minute")
def register_user(request: Request, user: schema.UserRegister, db: Session = Depends(get_db)):
    """
    Creates a new user.
    Ensures email and username are not duplicates.
    Role always defaults to "user" - see schema.UserRegister.
    """
    if repository.get_user_by_email(db, user.email):
        raise HTTPException(400, "Email already registered")

    if repository.get_user_by_username(db, user.username):
        raise HTTPException(400, "Username already taken")

    new_user = repository.create_user(db, user)
    return new_user


# -------------------------------------------------------------------
# LOGIN USER → RETURNS ACCESS + REFRESH TOKEN
# -------------------------------------------------------------------
@router.post("/login", response_model=schema.Token)
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login using username or email.
    Returns:
      - access_token (JWT)
      - refresh_token (stored in DB, with an expiry)
    """
    user = repository.get_user_by_username_or_email(db, form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create JWT with "sub"
    access_token = create_access_token({"sub": str(user.user_id)})

    # Create & save refresh token
    refresh_token_str, refresh_expires = create_refresh_token()
    repo.save_refresh_token(db, user.user_id, refresh_token_str, refresh_expires)

    return schema.Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token_str,
        refresh_expires_at=refresh_expires
    )


# -------------------------------------------------------------------
# REFRESH TOKEN → NEW ACCESS TOKEN
# -------------------------------------------------------------------
@router.post("/refresh", response_model=Dict[str, str])
@limiter.limit("30/minute")
def refresh(request: Request, payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Accepts a refresh token → returns new access token.
    """
    token_str = payload.refresh_token
    if not token_str:
        raise HTTPException(400, "refresh_token required")

    rt = repo.get_refresh_token(db, token_str)
    if not rt or rt.revoked:
        raise HTTPException(401, "Invalid refresh token")

    if rt.expires_at < datetime.now(timezone.utc):
        raise HTTPException(401, "Refresh token expired")

    new_access = create_access_token({"sub": str(rt.user_id)})

    return {"access_token": new_access, "token_type": "bearer"}


# -------------------------------------------------------------------
# LOGOUT → REVOKE REFRESH TOKEN
# -------------------------------------------------------------------
@router.post("/logout")
def logout(payload: Dict[str, str], db: Session = Depends(get_db)):
    """
    Revokes a refresh token, logging user out.
    """
    token_str = payload.get("refresh_token")
    if not token_str:
        raise HTTPException(400, "refresh_token required")

    rt = repo.revoke_refresh_token(db, token_str)
    if not rt:
        raise HTTPException(404, "Token not found")

    return {"detail": "Logged out successfully"}


# -------------------------------------------------------------------
# GET CURRENT USER INFO
# -------------------------------------------------------------------
@router.get("/me", response_model=schema.UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns logged-in user's profile.
    """
    return current_user


# -------------------------------------------------------------------
# UPDATE PROFILE (PARTIAL UPDATE)
# -------------------------------------------------------------------
@router.patch("/me", response_model=schema.UserResponse)
def update_profile(payload: schema.UserUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Update username or email of the logged-in user.

    Role is deliberately not editable here - see schema.UserUpdate.
    Use PATCH /auth/users/{user_id}/role (admin-only) to change roles.
    """
    changed = False

    if payload.username:
        current_user.username = payload.username
        changed = True

    if payload.email:
        current_user.email = payload.email
        changed = True

    if changed:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)

    return current_user


# -------------------------------------------------------------------
# ADMIN: CHANGE ANOTHER USER'S ROLE
# -------------------------------------------------------------------
@router.patch("/users/{user_id}/role", response_model=schema.UserResponse)
def update_user_role(
    user_id: UUID,
    payload: schema.RoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Change another user's global role. Admin only.

    Note: the very first admin must be promoted directly in the database
    (e.g. `UPDATE users SET role = 'admin' WHERE email = '...'`) since
    self-registration can no longer grant admin.
    """
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")

    target.role = payload.role
    db.add(target)
    db.commit()
    db.refresh(target)

    return target


# -------------------------------------------------------------------
# ADMIN-ONLY EXAMPLE
# -------------------------------------------------------------------
@router.get("/admin-only")
def admin_only(current_user: User = Depends(require_admin)):
    return {"detail": "Welcome Admin"}


# -------------------------------------------------------------------
# PASSWORD RESET (REQUEST)
# -------------------------------------------------------------------
@router.post("/password-reset/request")
@limiter.limit("3/minute")
def password_reset_request(request: Request, payload: Dict[str, str], db: Session = Depends(get_db)):
    """
    Generates a password reset token and (in a real deployment) emails it
    to the user.

    Always returns the same generic response whether or not the email is
    registered - returning a 404 only for unknown emails would let an
    attacker enumerate which addresses have accounts. There's no email
    sending set up yet, so the token is only included in the response
    when EXPOSE_PASSWORD_RESET_TOKEN=true (local/dev use only - never set
    this in production).
    """
    email = payload.get("email")
    if not email:
        raise HTTPException(400, "email required")

    user = repo.get_user_by_email(db, email)

    reset_token = None
    if user:
        reset_token = secrets.token_urlsafe(48)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        repo.create_password_reset_token(db, user.user_id, reset_token, expires_at)

    response = {"detail": "If an account exists for that email, a reset link has been sent."}
    if reset_token and os.getenv("EXPOSE_PASSWORD_RESET_TOKEN", "false").lower() == "true":
        response["reset_token"] = reset_token
    return response


# -------------------------------------------------------------------
# PASSWORD RESET (CONFIRM)
# -------------------------------------------------------------------
@router.post("/password-reset/confirm")
@limiter.limit("10/minute")
def password_reset_confirm(request: Request, payload: Dict[str, str], db: Session = Depends(get_db)):
    """
    Uses the reset token to change user's password.
    """
    token_str = payload.get("reset_token")
    new_password = payload.get("new_password")

    if not token_str or not new_password:
        raise HTTPException(400, "reset_token and new_password required")

    token_obj = repo.get_password_reset_token(db, token_str)

    if not token_obj or token_obj.used or token_obj.expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "Invalid or expired token")

    user = db.get(User, token_obj.user_id)
    if not user:
        raise HTTPException(404, "User not found")

    # Change password
    user.hashed_password = hash_password(new_password)
    db.add(user)

    # Mark token used
    repo.mark_password_reset_used(db, token_obj)
    db.commit()

    return {"detail": "Password updated successfully"}
