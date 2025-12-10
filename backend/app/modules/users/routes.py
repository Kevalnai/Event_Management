# app/module/users/router.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # For standard login form data
from sqlalchemy.orm import Session
from datetime import timedelta

# Relative Imports 
from ...core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from ...core.databse import get_db
from . import repository, schema
from .schema import UserRegister, UserResponse, Token

router = APIRouter(prefix="/users", tags=["Users"])

# --- (Existing) User Registration Endpoint ---
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    # ... (Registration logic from previous response) ...
    db_user_email = repository.get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered.")
        
    db_user_username = repository.get_user_by_username(db, username=user.username)
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username already taken.")

    return repository.create_user(db=db, user=user)

# --- (NEW) User Login Endpoint ---
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), # FastAPI utility for standard login forms
    db: Session = Depends(get_db)
):
    # 1. Retrieve the user by username (which can be username or email in our case)
    user_identifier = form_data.username # OAuth2PasswordRequestForm uses 'username'
    db_user = repository.get_user_by_username_or_email(db, identifier=user_identifier)
    
    # 2. Check if user exists and verify password
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        # Raise standard 401 for login failure
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Generate the JWT Access Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # The subject ('sub') of the token is the user's ID
    access_token = create_access_token(
        data={"user_id": str(db_user.user_id)}, 
        expires_delta=access_token_expires
    )
    
    # 4. Return the Token schema
    return {"access_token": access_token, "token_type": "bearer"}