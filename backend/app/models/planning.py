from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class DependencyType(str, enum.Enum):
    BLOCKS = "blocks"  # Source blocks target
    DEPENDS_ON = "depends_on"  # Source depends on target
    RELATED = "related"  # Informational relationship


class DependencyStatus(str, enum.Enum):
    PENDING = "pending"  # Dependency not yet resolved
    IN_PROGRESS = "in_progress"  # Being worked on
    RESOLVED = "resolved"  # Dependency satisfied
    BLOCKED = "blocked"  # External blocker


class ItemType(str, enum.Enum):
    EPIC = "epic"
    STORY = "story"
    TASK = "task"


class Dependency(Base):
    """Represents dependencies between work items (epics, stories, tasks)."""
    __tablename__ = "dependencies"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Source item (the one that has the dependency)
    source_type = Column(SQLEnum(ItemType), nullable=False)
    source_id = Column(Integer, nullable=False)

    # Target item (the one being depended upon)
    target_type = Column(SQLEnum(ItemType), nullable=False)
    target_id = Column(Integer, nullable=False)

    dependency_type = Column(SQLEnum(DependencyType), default=DependencyType.DEPENDS_ON)
    status = Column(SQLEnum(DependencyStatus), default=DependencyStatus.PENDING)

    # AI inference metadata
    inferred = Column(Boolean, default=False)  # True if AI-detected
    confidence = Column(Float, nullable=True)  # AI confidence score
    inference_reason = Column(Text, nullable=True)  # Why AI inferred this

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="dependencies")


class DecisionStatus(str, enum.Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"


class Decision(Base):
    """Architectural Decision Record (ADR) for project decisions."""
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    title = Column(String(255), nullable=False)
    context = Column(Text, nullable=True)  # Background and problem statement
    decision = Column(Text, nullable=False)  # The actual decision made
    rationale = Column(Text, nullable=True)  # Why this decision was made
    alternatives = Column(Text, nullable=True)  # Alternatives considered (JSON array)
    consequences = Column(Text, nullable=True)  # Expected consequences

    status = Column(SQLEnum(DecisionStatus), default=DecisionStatus.PROPOSED)
    decision_maker = Column(String(255), nullable=True)
    decision_date = Column(DateTime(timezone=True), nullable=True)

    # AI extraction metadata
    extracted_from = Column(String(50), nullable=True)  # e.g., "intake", "meeting", "prd"
    extraction_confidence = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="decisions")


class AssumptionStatus(str, enum.Enum):
    UNVALIDATED = "unvalidated"
    VALIDATING = "validating"
    VALIDATED = "validated"
    INVALIDATED = "invalidated"


class AssumptionRisk(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Assumption(Base):
    """Project assumptions that need validation."""
    __tablename__ = "assumptions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    assumption = Column(Text, nullable=False)  # The assumption itself
    context = Column(Text, nullable=True)  # Where/why this assumption was made
    impact_if_wrong = Column(Text, nullable=True)  # What happens if invalidated

    status = Column(SQLEnum(AssumptionStatus), default=AssumptionStatus.UNVALIDATED)
    risk_level = Column(SQLEnum(AssumptionRisk), default=AssumptionRisk.MEDIUM)

    # Validation tracking
    validation_method = Column(Text, nullable=True)  # How to validate
    validation_owner = Column(String(255), nullable=True)
    validation_deadline = Column(DateTime(timezone=True), nullable=True)
    validation_result = Column(Text, nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)

    # AI extraction metadata
    extracted_from = Column(String(50), nullable=True)
    extraction_confidence = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="assumptions")


class PrioritizationModel(str, enum.Enum):
    RICE = "rice"  # Reach, Impact, Confidence, Effort
    WSJF = "wsjf"  # Weighted Shortest Job First
    COD = "cod"  # Cost of Delay
    CUSTOM = "custom"


class StoryEstimate(Base):
    """Range estimates and prioritization scores for stories."""
    __tablename__ = "story_estimates"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False, unique=True)

    # Range estimates (in hours)
    estimate_p10 = Column(Float, nullable=True)  # Optimistic (10th percentile)
    estimate_p50 = Column(Float, nullable=True)  # Most likely (50th percentile)
    estimate_p90 = Column(Float, nullable=True)  # Pessimistic (90th percentile)

    # RICE scoring
    rice_reach = Column(Integer, nullable=True)  # How many users affected
    rice_impact = Column(Float, nullable=True)  # 0.25, 0.5, 1, 2, 3 scale
    rice_confidence = Column(Float, nullable=True)  # 0.5, 0.8, 1.0 scale
    rice_effort = Column(Float, nullable=True)  # Person-months
    rice_score = Column(Float, nullable=True)  # Calculated score

    # WSJF scoring
    wsjf_business_value = Column(Integer, nullable=True)  # 1-21 Fibonacci
    wsjf_time_criticality = Column(Integer, nullable=True)  # 1-21 Fibonacci
    wsjf_risk_reduction = Column(Integer, nullable=True)  # 1-21 Fibonacci (also opportunity enablement)
    wsjf_job_size = Column(Integer, nullable=True)  # 1-21 Fibonacci
    wsjf_score = Column(Float, nullable=True)  # Calculated score

    # Cost of Delay
    cod_weekly = Column(Float, nullable=True)  # Weekly cost of delay in $
    cod_urgency_profile = Column(String(50), nullable=True)  # linear, exponential, fixed_date

    # OKR alignment
    okr_alignment_score = Column(Float, nullable=True)  # 0-100 alignment with OKRs
    aligned_okrs = Column(Text, nullable=True)  # JSON array of aligned OKR IDs/names

    # AI-generated estimates
    ai_estimate_p10 = Column(Float, nullable=True)
    ai_estimate_p50 = Column(Float, nullable=True)
    ai_estimate_p90 = Column(Float, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_reasoning = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    story = relationship("Story", back_populates="estimate")
