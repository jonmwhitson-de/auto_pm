from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class IntakeSource(str, enum.Enum):
    SLACK = "slack"
    TEAMS = "teams"
    EMAIL = "email"
    MEETING_TRANSCRIPT = "meeting_transcript"
    SUPPORT_TICKET = "support_ticket"
    SALES_REQUEST = "sales_request"
    DOCUMENT = "document"
    MANUAL = "manual"


class IntakeType(str, enum.Enum):
    BUG = "bug"
    FEATURE = "feature"
    TECH_DEBT = "tech_debt"
    RISK = "risk"
    COMPLIANCE = "compliance"
    ENHANCEMENT = "enhancement"
    UNKNOWN = "unknown"


class IntakeStatus(str, enum.Enum):
    NEW = "new"
    TRIAGING = "triaging"
    NEEDS_CLARIFICATION = "needs_clarification"
    READY = "ready"
    CONVERTED = "converted"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"


class Intake(Base):
    """Incoming request from any channel before it becomes a formal initiative."""
    __tablename__ = "intakes"

    id = Column(Integer, primary_key=True, index=True)

    # Source information
    source = Column(SQLEnum(IntakeSource), default=IntakeSource.MANUAL)
    source_id = Column(String(255), nullable=True)  # External reference ID
    source_url = Column(Text, nullable=True)
    source_author = Column(String(255), nullable=True)
    source_channel = Column(String(255), nullable=True)  # Slack channel, email thread, etc.

    # Raw content
    title = Column(String(500), nullable=False)
    raw_content = Column(Text, nullable=False)

    # AI-inferred classification
    inferred_type = Column(SQLEnum(IntakeType), default=IntakeType.UNKNOWN)
    type_confidence = Column(Float, default=0.0)

    # Priority scoring
    priority_score = Column(Float, nullable=True)
    priority_rationale = Column(Text, nullable=True)

    # Status
    status = Column(SQLEnum(IntakeStatus), default=IntakeStatus.NEW)

    # Duplicate detection
    duplicate_of_id = Column(Integer, ForeignKey("intakes.id"), nullable=True)
    duplicate_confidence = Column(Float, nullable=True)

    # Conversion
    converted_to_project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Timestamps
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    triaged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    pm_brief = relationship("PMBrief", back_populates="intake", uselist=False, cascade="all, delete-orphan")
    clarifying_questions = relationship("ClarifyingQuestion", back_populates="intake", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="intake", cascade="all, delete-orphan")
    stakeholders = relationship("IntakeStakeholder", back_populates="intake", cascade="all, delete-orphan")
    duplicate_of = relationship("Intake", remote_side=[id])
    converted_to_project = relationship("Project")


class PMBrief(Base):
    """Structured PM brief extracted from intake."""
    __tablename__ = "pm_briefs"

    id = Column(Integer, primary_key=True, index=True)
    intake_id = Column(Integer, ForeignKey("intakes.id"), nullable=False, unique=True)

    # Problem & Context
    problem_statement = Column(Text, nullable=True)
    target_users = Column(Text, nullable=True)  # JSON array of user types
    use_cases = Column(Text, nullable=True)  # JSON array

    # Metrics
    north_star_metric = Column(String(500), nullable=True)
    input_metrics = Column(Text, nullable=True)  # JSON array

    # Constraints
    security_constraints = Column(Text, nullable=True)
    privacy_constraints = Column(Text, nullable=True)
    performance_constraints = Column(Text, nullable=True)  # latency, throughput
    budget_constraints = Column(Text, nullable=True)
    compatibility_constraints = Column(Text, nullable=True)

    # Scope
    assumptions = Column(Text, nullable=True)  # JSON array
    out_of_scope = Column(Text, nullable=True)  # JSON array
    acceptance_criteria = Column(Text, nullable=True)  # JSON array of testable criteria

    # Dependencies
    team_dependencies = Column(Text, nullable=True)  # JSON array
    service_dependencies = Column(Text, nullable=True)  # JSON array
    vendor_dependencies = Column(Text, nullable=True)  # JSON array

    # Extraction metadata
    extraction_confidence = Column(Float, default=0.0)
    missing_fields = Column(Text, nullable=True)  # JSON array of field names

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    intake = relationship("Intake", back_populates="pm_brief")


class ClarifyingQuestion(Base):
    """Questions generated to reduce ambiguity."""
    __tablename__ = "clarifying_questions"

    id = Column(Integer, primary_key=True, index=True)
    intake_id = Column(Integer, ForeignKey("intakes.id"), nullable=False)

    question = Column(Text, nullable=False)
    context = Column(Text, nullable=True)  # Why this question matters
    target_field = Column(String(100), nullable=True)  # Which PM brief field this clarifies

    # Routing
    assigned_to = Column(String(255), nullable=True)  # Who should answer
    assigned_to_email = Column(String(255), nullable=True)

    # Response
    answer = Column(Text, nullable=True)
    answered_by = Column(String(255), nullable=True)
    answered_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_blocking = Column(Boolean, default=False)
    is_answered = Column(Boolean, default=False)

    # Priority (1 = highest ambiguity reduction)
    priority = Column(Integer, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    intake = relationship("Intake", back_populates="clarifying_questions")


class Artifact(Base):
    """Linked documents, transcripts, tickets, etc."""
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    intake_id = Column(Integer, ForeignKey("intakes.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Artifact info
    name = Column(String(500), nullable=False)
    artifact_type = Column(String(100), nullable=False)  # prd, spec, diagram, meeting_note, contract, support_thread
    url = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # For inline content

    # Metadata
    source = Column(String(100), nullable=True)  # google_docs, confluence, notion, etc.
    external_id = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    intake = relationship("Intake", back_populates="artifacts")


class IntakeStakeholder(Base):
    """Stakeholders identified for an intake."""
    __tablename__ = "intake_stakeholders"

    id = Column(Integer, primary_key=True, index=True)
    intake_id = Column(Integer, ForeignKey("intakes.id"), nullable=False)

    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    role = Column(String(100), nullable=True)  # decision_maker, contributor, informed

    # Influence/Interest matrix
    influence = Column(String(20), default="medium")  # low, medium, high
    interest = Column(String(20), default="medium")  # low, medium, high

    # Communication preferences
    preferred_channel = Column(String(50), nullable=True)  # email, slack, teams
    communication_cadence = Column(String(50), nullable=True)  # daily, weekly, milestone

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    intake = relationship("Intake", back_populates="stakeholders")
