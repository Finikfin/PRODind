import uuid
import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey, Float, Table, Column, UniqueConstraint, Index, Integer, CheckConstraint
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
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

class ExperimentOutcome(str, enum.Enum):
    ROLLOUT = "ROLLOUT"
    ROLLBACK = "ROLLBACK"
    NO_EFFECT = "NO_EFFECT"

class GuardrailAction(str, enum.Enum):
    PAUSE = "PAUSE"
    ROLLBACK = "ROLLBACK"

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

class ConflictDomain(Base):
    __tablename__ = "conflict_domains"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)

class Flag(Base):
    __tablename__ = "flags"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    default_value: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    experiments: Mapped[List["Experiment"]] = relationship("Experiment", back_populates="flag", cascade="all, delete-orphan")

class ExperimentApproval(Base):
    __tablename__ = "experiment_approvals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"))
    approver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="approvals")

    __table_args__ = (UniqueConstraint("experiment_id", "approver_id", name="uq_experiment_approver"),)

class Experiment(Base):
    __tablename__ = "experiments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("flags.id", ondelete="CASCADE"), index=True)
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    conflict_domain_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("conflict_domains.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[ExperimentStatus] = mapped_column(SQLEnum(ExperimentStatus), default=ExperimentStatus.DRAFT, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    audience_share: Mapped[float] = mapped_column(Float, default=1.0)
    targeting_rules: Mapped[Optional[dict]] = mapped_column(JSONB)
    variants: Mapped[dict] = mapped_column(JSONB)
    conclusion: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    outcome: Mapped[Optional[ExperimentOutcome]] = mapped_column(SQLEnum(ExperimentOutcome), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    flag: Mapped["Flag"] = relationship("Flag", back_populates="experiments")
    creator: Mapped["User"] = relationship("User", back_populates="created_experiments")
    approvals: Mapped[List["ExperimentApproval"]] = relationship("ExperimentApproval", back_populates="experiment", cascade="all, delete-orphan")
    guardrails: Mapped[List["Guardrail"]] = relationship("Guardrail", back_populates="experiment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("uq_flag_running_idx", flag_id, status, unique=True, postgresql_where=(status == ExperimentStatus.RUNNING)),
        CheckConstraint("audience_share >= 0 AND audience_share <= 1", name="check_audience_share_range"),
    )

class Exposure(Base):
    __tablename__ = "exposures"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id"), index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(index=True)
    variant_name: Mapped[str] = mapped_column(String(50))
    decision_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class Conversion(Base):
    __tablename__ = "conversions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(index=True)
    goal_type: Mapped[str] = mapped_column(String(50), index=True)
    decision_id: Mapped[str] = mapped_column(String(64), ForeignKey("exposures.decision_id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class Guardrail(Base):
    __tablename__ = "guardrails"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), index=True)
    metric_key: Mapped[str] = mapped_column(String(100))
    threshold: Mapped[float] = mapped_column(Float)
    operator: Mapped[str] = mapped_column(String(10), default=">")
    action: Mapped[GuardrailAction] = mapped_column(SQLEnum(GuardrailAction), default=GuardrailAction.PAUSE)
    is_triggered: Mapped[bool] = mapped_column(default=False)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="guardrails")