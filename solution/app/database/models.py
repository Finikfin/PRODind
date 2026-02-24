import uuid
import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey, Float, Table, Column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

approver_experimenter_association = Table(
    "approver_experimenter_association",
    Base.metadata,
    Column("experimenter_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")),
    Column("approver_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")),
)

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    APPROVER = "APPROVER"
    EXPERIMENTER = "EXPERIMENTER"

class ExperimentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ON_REVIEW = "ON_REVIEW"
    APPROVED = "APPROVED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.EXPERIMENTER)
    min_approvals_required: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(default=True) 
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    created_experiments: Mapped[List["Experiment"]] = relationship("Experiment", back_populates="creator")
    allowed_approvers: Mapped[List["User"]] = relationship(
        "User",
        secondary=approver_experimenter_association,
        primaryjoin=id == approver_experimenter_association.c.experimenter_id,
        secondaryjoin=id == approver_experimenter_association.c.approver_id,
        backref="assigned_experimenters"
    )

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

    experiments: Mapped[List["Experiment"]] = relationship("Experiment", back_populates="flag", cascade="all, delete-orphan")

class ConflictDomain(Base):
    __tablename__ = "conflict_domains"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("flags.id", ondelete="CASCADE"))
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    conflict_domain_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("conflict_domains.id", ondelete="SET NULL"), nullable=True)
    domain_offset: Mapped[int] = mapped_column(default=0)
    
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    status: Mapped[ExperimentStatus] = mapped_column(SQLEnum(ExperimentStatus), default=ExperimentStatus.DRAFT)
    audience_share: Mapped[float] = mapped_column(Float, default=1.0)
    targeting_rules: Mapped[Optional[dict]] = mapped_column(JSONB)
    variants: Mapped[dict] = mapped_column(JSONB)
    conclusion: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    flag: Mapped["Flag"] = relationship("Flag", back_populates="experiments")
    creator: Mapped["User"] = relationship("User", back_populates="created_experiments")
    conflict_domain: Mapped[Optional["ConflictDomain"]] = relationship("ConflictDomain")
    approvals: Mapped[List["ExperimentApproval"]] = relationship("ExperimentApproval", cascade="all, delete-orphan")

class ExperimentApproval(Base):
    __tablename__ = "experiment_approvals"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"))
    approver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Exposure(Base):
    __tablename__ = "exposures"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id"))
    subject_id: Mapped[uuid.UUID] = mapped_column(index=True)
    variant_name: Mapped[str] = mapped_column(String(50))
    decision_id: Mapped[str] = mapped_column(String(50), unique=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Conversion(Base):
    __tablename__ = "conversions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(index=True)
    goal_type: Mapped[str] = mapped_column(String(50))
    properties: Mapped[dict] = mapped_column(JSONB, nullable=True)
    decision_id: Mapped[str] = mapped_column(String(50), ForeignKey("exposures.decision_id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)