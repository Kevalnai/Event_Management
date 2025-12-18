# User models.py
from sqlalchemy import String, DateTime, func, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4

from app.core.database import Base


class User(Base):
    """
    SQLAlchemy Model defining the 'users' table in PostgreSQL.
    """
    __tablename__ = "users"

    # Primary Key and Metadata
    # Uses server_default for auto-generation by the database
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Core User Data
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    role: Mapped[str] = mapped_column(String(20), default="user")
    
    # Security Field (Stored in DB, NOT exposed to clients)
    hashed_password: Mapped[str] = mapped_column(String)

    event_organisers = relationship(
        "EventOrganiser",
        back_populates="user",
        cascade="all, delete-orphan"
    )


    event_registrations = relationship(
        "EventRegistration",
        back_populates="user"
    )

    # relationship to refresh tokens and reset tokens (optional)
    
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )


    def __repr__(self):
        return f"User(id={self.user_id}, username='{self.username}', role='{self.role}')"
    

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id",ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.revoked})"
    

class PasswordResetToken(Base):
    """
    One-time password reset token stored in DB (short expiry).
    You can later send this token to user's email.
    """
    __tablename__ = "password_reset_tokens"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="password_reset_tokens")

    def __repr__(self):
        return f"PasswordResetToken(id={self.id}, user_id={self.user_id}, used={self.used})" 