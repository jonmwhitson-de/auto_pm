from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    estimated_hours = Column(Integer, nullable=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.TODO)
    order = Column(Integer, default=0)
    assigned_to_id = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    story = relationship("Story", back_populates="tasks")
    assigned_to = relationship("TeamMember", back_populates="assigned_tasks")
