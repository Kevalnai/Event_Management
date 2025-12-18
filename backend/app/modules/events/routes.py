# Routes.py
# Handles HTTP only
# Converts errors to HTTP responses
# Uses FastAPI dependencies

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from .schema import (
    EventCreate,
    EventRead,
    EventUpdate,
    EventDetail
)
from .services import EventService
from ...core.databse import get_db
from ..users.auth import get_current_user
from .models import User

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return EventService.create_event(
            db=db,
            payload=payload,
            user_id=current_user.user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{event_id}", response_model=EventDetail)
def get_event(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    try:
        return EventService.get_event(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: UUID,
    payload: EventUpdate,
    db: Session = Depends(get_db)
):
    try:
        return EventService.update_event(db, event_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    try:
        EventService.delete_event(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
