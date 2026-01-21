from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, ForeignKey,
    Boolean, Float, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class LifecyclePhase(str, enum.Enum):
    """Offer Lifecycle phases in sequential order."""
    CONCEPT = "concept"
    DEFINE = "define"
    PLAN = "plan"
    DEVELOP = "develop"
    LAUNCH = "launch"
    SUSTAIN = "sustain"


class PhaseStatus(str, enum.Enum):
    """Status of a lifecycle phase."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SKIPPED = "skipped"


class ServiceTaskStatus(str, enum.Enum):
    """Status of a service task."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    NOT_APPLICABLE = "not_applicable"


class TaskSource(str, enum.Enum):
    """Source of task creation."""
    AI_GENERATED = "ai_generated"
    TEMPLATE = "template"
    MANUAL = "manual"


# Phase order mapping for sequential logic
PHASE_ORDER = {
    LifecyclePhase.CONCEPT: 1,
    LifecyclePhase.DEFINE: 2,
    LifecyclePhase.PLAN: 3,
    LifecyclePhase.DEVELOP: 4,
    LifecyclePhase.LAUNCH: 5,
    LifecyclePhase.SUSTAIN: 6,
}


class OfferLifecyclePhase(Base):
    """Represents an Offer Lifecycle phase for a project."""
    __tablename__ = "offer_lifecycle_phases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    phase = Column(SQLEnum(LifecyclePhase), nullable=False)
    status = Column(SQLEnum(PhaseStatus), default=PhaseStatus.NOT_STARTED)
    order = Column(Integer, nullable=False)

    # Approval tracking
    approval_required = Column(Boolean, default=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)

    # Override tracking
    sequence_overridden = Column(Boolean, default=False)
    override_reason = Column(Text, nullable=True)
    overridden_by = Column(String(255), nullable=True)
    overridden_at = Column(DateTime(timezone=True), nullable=True)

    # Target dates
    target_start_date = Column(Date, nullable=True)
    target_end_date = Column(Date, nullable=True)

    # Actual dates
    actual_start_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="lifecycle_phases")
    service_tasks = relationship(
        "ServiceTask",
        back_populates="phase",
        cascade="all, delete-orphan",
        order_by="ServiceTask.order"
    )

    # Unique constraint: one phase per project per phase type
    __table_args__ = (
        UniqueConstraint('project_id', 'phase', name='uq_project_phase'),
    )


class ServiceTask(Base):
    """Service-focused checklist item for Offer Lifecycle tracking."""
    __tablename__ = "service_tasks"

    id = Column(Integer, primary_key=True, index=True)
    phase_id = Column(Integer, ForeignKey("offer_lifecycle_phases.id"), nullable=False)

    # Task definition
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    definition = Column(Text, nullable=True)

    # Categorization
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)

    # Status and tracking
    status = Column(SQLEnum(ServiceTaskStatus), default=ServiceTaskStatus.NOT_STARTED)
    source = Column(SQLEnum(TaskSource), default=TaskSource.AI_GENERATED)

    # Scheduling
    target_start_date = Column(Date, nullable=True)
    target_complete_date = Column(Date, nullable=True)
    days_required = Column(Integer, nullable=True)
    actual_start_date = Column(Date, nullable=True)
    actual_complete_date = Column(Date, nullable=True)

    # Assignment
    owner = Column(String(255), nullable=True)
    team = Column(String(100), nullable=True)

    # Dependencies (optional linking to dev work)
    linked_epic_id = Column(Integer, ForeignKey("epics.id"), nullable=True)
    linked_story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)

    # Ordering and grouping
    order = Column(Integer, default=0)
    is_required = Column(Boolean, default=True)

    # AI generation metadata
    ai_confidence = Column(Float, nullable=True)
    ai_reasoning = Column(Text, nullable=True)
    template_id = Column(String(50), nullable=True)

    # Notes and artifacts
    notes = Column(Text, nullable=True)
    completion_notes = Column(Text, nullable=True)
    artifacts_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    phase = relationship("OfferLifecyclePhase", back_populates="service_tasks")
    linked_epic = relationship("Epic", foreign_keys=[linked_epic_id])
    linked_story = relationship("Story", foreign_keys=[linked_story_id])
