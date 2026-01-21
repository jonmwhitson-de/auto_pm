from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models import Story
from app.models.epic import Priority
from app.models.story import StoryStatus

router = APIRouter()


class StoryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    story_points: Optional[int] = None
    estimated_hours: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    sprint_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    order: Optional[int] = None


class StoryResponse(BaseModel):
    id: int
    epic_id: int
    sprint_id: Optional[int]
    title: str
    description: Optional[str]
    acceptance_criteria: Optional[str]
    story_points: Optional[int]
    estimated_hours: Optional[int]
    priority: str
    status: str
    order: int

    class Config:
        from_attributes = True


@router.get("/{story_id}")
def get_story(story_id: int, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.patch("/{story_id}", response_model=StoryResponse)
def update_story(story_id: int, update: StoryUpdate, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    if update.title is not None:
        story.title = update.title
    if update.description is not None:
        story.description = update.description
    if update.acceptance_criteria is not None:
        story.acceptance_criteria = update.acceptance_criteria
    if update.story_points is not None:
        story.story_points = update.story_points
    if update.estimated_hours is not None:
        story.estimated_hours = update.estimated_hours
    if update.priority is not None:
        story.priority = Priority(update.priority)
    if update.status is not None:
        story.status = StoryStatus(update.status)
    if update.sprint_id is not None:
        story.sprint_id = update.sprint_id if update.sprint_id != 0 else None
    if update.assigned_to_id is not None:
        story.assigned_to_id = update.assigned_to_id if update.assigned_to_id != 0 else None
    if update.order is not None:
        story.order = update.order

    db.commit()
    db.refresh(story)
    return {
        "id": story.id,
        "epic_id": story.epic_id,
        "sprint_id": story.sprint_id,
        "title": story.title,
        "description": story.description,
        "acceptance_criteria": story.acceptance_criteria,
        "story_points": story.story_points,
        "estimated_hours": story.estimated_hours,
        "priority": story.priority.value,
        "status": story.status.value,
        "order": story.order,
    }


@router.delete("/{story_id}")
def delete_story(story_id: int, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    db.delete(story)
    db.commit()
    return {"message": "Story deleted"}
