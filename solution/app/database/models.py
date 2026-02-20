import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    APPROVER = "APPROVER"
    EXPERIMENTER = "EXPERIMENTER"

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.EXPERIMENTER)
    is_active: Mapped[bool] = mapped_column(default=True) 
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Flag(Base):
    __tablename__ = "flags"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    type: Mapped[str] = mapped_column(String(20), default="boolean")
    is_active: Mapped[bool] = mapped_column(default=True) 
    default_value: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)