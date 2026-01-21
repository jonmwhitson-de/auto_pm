from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.epic import Priority
import enum


class StoryStatus(str, enum.Enum):
    BACKLOG = "backlog"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    epic_id = Column(Integer, ForeignKey("epics.id"), nullable=False)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)
    story_points = Column(Integer, nullable=True)
    estimated_hours = Column(Integer, nullable=True)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM)
    status = Column(SQLEnum(StoryStatus), default=StoryStatus.BACKLOG)
    order = Column(Integer, default=0)
    assigned_to_id = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    epic = relationship("Epic", back_populates="stories")
    sprint = relationship("Sprint", back_populates="stories")
    tasks = relationship("Task", back_populates="story", cascade="all, delete-orphan")
    assigned_to = relationship("TeamMember", back_populates="assigned_stories")
    estimate = relationship("StoryEstimate", back_populates="story", uselist=False, cascade="all, delete-orphan")
