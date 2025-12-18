# # auth.py

# import secrets
# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from sqlalchemy.orm import Session
# from datetime import datetime, timedelta
# from jose import jwt, JWTError, ExpiredSignatureError
# from uuid import UUID
# from typing import Dict

# from . import schema, repository
# from ...core.databse import get_db
# from .services import verify_password
# from .models import User
# from .schema import RefreshTokenRequest
# from . import schema
# from . import repository as repo # your repository (or repository_extended)
# from . import services

# # -------------------------------------------------------------------
# # JWT Settings
# # -------------------------------------------------------------------
# SECRET_KEY = "YOUR_SECRET_KEY_CHANGE_THIS"  # Replace with environment variable in production
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# # OAuth2 scheme (FastAPI will look for token in Authorization: Bearer <token>)
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# router = APIRouter(prefix="/auth", tags=["Authentication"])


# # -------------------------------------------------------------------
# # Create JWT Access Token
# # -------------------------------------------------------------------
# def create_access_token(data: dict, expires_delta: timedelta | None = None):
#     """
#     Generates a JWT token with expiry.
#     """
#     to_encode = data.copy()

#     expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp": expire})

#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt


# # -------------------------------------------------------------------
# # Get Current Authenticated User
# # -------------------------------------------------------------------
# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     """
#     Validates JWT and returns the current user.
#     """
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = payload.get("sub")

#         if user_id is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token (missing sub))")

#     except ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token has expired")
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")

#     try:
#         user_uuid = UUID(user_id)
#     except ValueError:
#         raise HTTPException(status_code=401, detail="Invalid user ID format in token")
    
#     #Fetch user from database
#     user = db.get(User, user_id)

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     return user


# # -------------------------------------------------------------------
# # Register User
# # -------------------------------------------------------------------
# @router.post("/register", response_model=schema.UserResponse)
# def register_user(user: schema.UserRegister, db: Session = Depends(get_db)):
#     """
#     Registers a new user.
#     Checks for duplicate email or username.
#     """
#     # Check duplicates
#     if repository.get_user_by_email(db, user.email):
#         raise HTTPException(status_code=400, detail="Email already registered")

#     if repository.get_user_by_username(db, user.username):
#         raise HTTPException(status_code=400, detail="Username already taken")

#     # Create new user
#     new_user = repository.create_user(db, user)
#     return new_user


# # -------------------------------------------------------------------
# # Login User
# # -------------------------------------------------------------------
# @router.post("/login", response_model=schema.Token)
# def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     """
#     Performs login and returns JWT token.
#     Accepts username or email (both allowed).
#     """

#     # Fetch user via username_or_email logic
#     user = repository.get_user_by_username_or_email(db, form_data.username)

#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     # Verify password using passlib
#     if not verify_password(form_data.password, user.hashed_password):
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     # Create token payload
#     access_token = create_access_token({"user_id": str(user.user_id)})
#     refresh_token_str, refresh_expires = services.create_refresh_token()
#     repo.save_refresh_token(db, user.user_id, refresh_token_str)

#     return schema.Token(
#         access_token=access_token,
#         token_type="bearer",
#         refresh_token=refresh_token_str, # ONLY the string
#         expire = refresh_expires  
# )




# #--- Refresh: exchange valid refresh for new access ---

# @router.post("/refresh", response_model=Dict[str, str])
# def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
#     """
#     Expects JSON: { "refresh_token": "" }
#     """
#     token_str = payload.refresh_token
#     if not token_str:
#         raise HTTPException(status_code=400, detail="refresh_token required")

#     rt = repo.get_refresh_token(db, token_str)
#     if not rt or rt.revoked:
#         raise HTTPException(status_code=401, detail="Invalid refresh token")

#     # create new access token
#     access_token = services.create_access_token(str(rt.user_id))
#     return {"access_token": access_token, "token_type": "bearer"}


# #--- Logout: revoke a refresh token ---

# @router.post("/logout")
# def logout(payload: Dict[str, str], db: Session = Depends(get_db)):
#     token_str = payload.get("refresh_token")
#     if not token_str:
#         raise HTTPException(status_code=400, detail="refresh_token required")
#     rt = repo.revoke_refresh_token(db, token_str)
#     if not rt:
#         raise HTTPException(status_code=404, detail="Token not found")
#     return {"detail": "logged out"}

# #--- Get current user dependency ---

# # def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
# #     from jose import JWTError, ExpiredSignatureError
# #     from jose import jwt as jose_jwt

# #     try:
# #         payload = jose_jwt.decode(token, services.SECRET_KEY, algorithms=[services.ALGORITHM])
# #         user_id = payload.get("sub")
# #         if not user_id:
# #             raise HTTPException(status_code=401, detail="Invalid token1")
# #     except ExpiredSignatureError:
# #         raise HTTPException(status_code=401, detail="Token expired")
# #     except JWTError:
# #         raise HTTPException(status_code=401, detail="Invalid token2")

# #     try:
# #         user_uuid = UUID(user_id)
# #     except ValueError:
# #         raise HTTPException(status_code=401, detail="Invalid user id format")

# #     user = db.get(repo.models.User, user_uuid)
# #     if not user:
# #         raise HTTPException(status_code=404, detail="User not found")
# #     return user


# # -------------------------------------------------------------------
# # Example Protected Route
# # -------------------------------------------------------------------
# @router.get("/me", response_model=schema.UserResponse)
# def get_me(current_user: User = Depends(get_current_user)):
#     """
#     Returns the currently authenticated user's data.
#     """
#     return current_user

# #--- Update profile (partial) ---

# @router.patch("/me", response_model=schema.UserResponse)
# def update_profile(payload: schema.UserUpdate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
#     changed = False
#     if payload.username:
#         current_user.username = payload.username
#         changed = True
#     if payload.email:
#         current_user.email = payload.email
#         changed = True
#     if payload.role:
#         current_user.role = payload.role
#         changed = True
#     if changed:
#         db.add(current_user)
#         db.commit()
#         db.refresh(current_user)
#     return current_user

# #--- Role-protected example ---

# def require_admin(user):
#     if user.role != "admin":
#         raise HTTPException(status_code=403, detail="Admin only")

# @router.get("/admin-only")
# def admin_only(current_user = Depends(get_current_user)):
#     require_admin(current_user)
#     return {"detail": "hello admin"}

# #--- Password reset request (issues token you can email) ---

# @router.post("/password-reset/request")
# def password_reset_request(payload: Dict[str, str], db: Session = Depends(get_db)):
#     """
#     Expects: { "email": "user@example.com" }
#     Returns a reset token that you should email to the user.
#     """
#     email = payload.get("email")
#     if not email:
#         raise HTTPException(status_code=400, detail="email required")
#     user = repo.get_user_by_email(db, email)
#     if not user:
#     # don't reveal user-not-found in production; return 200 success
#         raise HTTPException(status_code=404, detail="User not found")

#     # generate one-time token and expiry
#     reset_token = secrets.token_urlsafe(48)
#     expires_at = datetime.utcnow() + timedelta(hours=1)
#     repo.create_password_reset_token(db, user.user_id, reset_token, expires_at)

#     # In production, send this token by email. Here we return it for demo.
#     return {"reset_token": reset_token, "expires_at": expires_at.isoformat()}


# #--- Password reset (consume token) ---

# @router.post("/password-reset/confirm")
# def password_reset_confirm(payload: Dict[str, str], db: Session = Depends(get_db)):
#     """
#     Expects: { "reset_token": "...", "new_password": "..." }
#     """
#     token_str = payload.get("reset_token")
#     new_password = payload.get("new_password")
#     if not token_str or not new_password:
#         raise HTTPException(status_code=400, detail="reset_token and new_password required")

#     token_obj = repo.get_password_reset_token(db, token_str)
#     if not token_obj or token_obj.used or token_obj.expires_at < datetime.now():
#         raise HTTPException(status_code=400, detail="Invalid or expired token")

#     user = db.get(repo.models.User, token_obj.user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     # update password
#     user.hashed_password = services.hash_password(new_password)
#     db.add(user)
#     # mark token used
#     repo.mark_password_reset_used(db, token_obj)
#     db.commit()
#     return {"detail": "password updated"}


# auth.py

import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt, JWTError, ExpiredSignatureError
from uuid import UUID
from typing import Dict

from . import schema, repository
from ...core.database import get_db
from .services import verify_password, hash_password, create_refresh_token
from .models import User
from .schema import RefreshTokenRequest
from . import repository as repo

# -------------------------------------------------------------------
# JWT CONFIG
# -------------------------------------------------------------------
SECRET_KEY = "YOUR_SECRET_KEY_CHANGE_THIS"   # replace in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

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
    
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
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


# -------------------------------------------------------------------
# REGISTER USER
# -------------------------------------------------------------------
@router.post("/register", response_model=schema.UserResponse)
def register_user(user: schema.UserRegister, db: Session = Depends(get_db)):
    """
    Creates a new user.
    Ensures email and username are not duplicates.
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
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login using username or email.
    Returns:
      - access_token (JWT)
      - refresh_token (stored in DB)
    """
    user = repository.get_user_by_username_or_email(db, form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create JWT with "sub"
    access_token = create_access_token({"sub": str(user.user_id)})

    # Create & save refresh token
    refresh_token_str, refresh_expires = create_refresh_token()
    repo.save_refresh_token(db, user.user_id, refresh_token_str)

    return schema.Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token_str,
        expire=refresh_expires
    )


# -------------------------------------------------------------------
# REFRESH TOKEN → NEW ACCESS TOKEN
# -------------------------------------------------------------------
@router.post("/refresh", response_model=Dict[str, str])
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Accepts a refresh token → returns new access token.
    """
    token_str = payload.refresh_token
    if not token_str:
        raise HTTPException(400, "refresh_token required")

    rt = repo.get_refresh_token(db, token_str)
    if not rt or rt.revoked:
        raise HTTPException(401, "Invalid refresh token")

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
    Update username, email, or role of the logged-in user.
    """
    changed = False

    if payload.username:
        current_user.username = payload.username
        changed = True

    if payload.email:
        current_user.email = payload.email
        changed = True

    if payload.role:
        current_user.role = payload.role
        changed = True

    if changed:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)

    return current_user


# -------------------------------------------------------------------
# ADMIN-ONLY EXAMPLE
# -------------------------------------------------------------------
def require_admin(user):
    if user.role != "admin":
        raise HTTPException(403, "Admin only")


@router.get("/admin-only")
def admin_only(current_user=Depends(get_current_user)):
    require_admin(current_user)
    return {"detail": "Welcome Admin"}


# -------------------------------------------------------------------
# PASSWORD RESET (REQUEST)
# -------------------------------------------------------------------
@router.post("/password-reset/request")
def password_reset_request(payload: Dict[str, str], db: Session = Depends(get_db)):
    """
    Generates a password reset token.
    In production, email this to the user.
    """
    email = payload.get("email")
    if not email:
        raise HTTPException(400, "email required")

    user = repo.get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User not found")

    reset_token = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    repo.create_password_reset_token(db, user.user_id, reset_token, expires_at)

    return {"reset_token": reset_token, "expires_at": expires_at.isoformat()}


# -------------------------------------------------------------------
# PASSWORD RESET (CONFIRM)
# -------------------------------------------------------------------
@router.post("/password-reset/confirm")
def password_reset_confirm(payload: Dict[str, str], db: Session = Depends(get_db)):
    """
    Uses the reset token to change user's password.
    """
    token_str = payload.get("reset_token")
    new_password = payload.get("new_password")

    if not token_str or not new_password:
        raise HTTPException(400, "reset_token and new_password required")

    token_obj = repo.get_password_reset_token(db, token_str)

    if not token_obj or token_obj.used or token_obj.expires_at < datetime.now():
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
