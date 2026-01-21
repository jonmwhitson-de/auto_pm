from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    prd_content = Column(Text, nullable=False)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    epics = relationship("Epic", back_populates="project", cascade="all, delete-orphan")
    sprints = relationship("Sprint", back_populates="project", cascade="all, delete-orphan")
    team_members = relationship("TeamMember", back_populates="project", cascade="all, delete-orphan")
    dependencies = relationship("Dependency", back_populates="project", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="project", cascade="all, delete-orphan")
    assumptions = relationship("Assumption", back_populates="project", cascade="all, delete-orphan")
    lifecycle_phases = relationship(
        "OfferLifecyclePhase",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="OfferLifecyclePhase.order"
    )
