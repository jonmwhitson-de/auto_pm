from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.models import Sprint, Story, Project
from app.models.sprint import SprintStatus
from app.core.config import settings

router = APIRouter()


class SprintCreate(BaseModel):
    project_id: int
    name: str
    goal: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    capacity_hours: Optional[int] = None


class SprintUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    capacity_hours: Optional[int] = None
    status: Optional[str] = None


class SprintResponse(BaseModel):
    id: int
    project_id: int
    name: str
    goal: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    capacity_hours: Optional[int]
    status: str
    order: int
    stories: list

    class Config:
        from_attributes = True


class SprintPlanRequest(BaseModel):
    sprint_id: int
    story_ids: list[int]


@router.get("/project/{project_id}")
def list_sprints(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sprints = db.query(Sprint).filter(Sprint.project_id == project_id).order_by(Sprint.order).all()
    result = []
    for sprint in sprints:
        stories = [
            {
                "id": s.id,
                "title": s.title,
                "story_points": s.story_points,
                "estimated_hours": s.estimated_hours,
                "status": s.status.value,
            }
            for s in sprint.stories
        ]
        result.append({
            "id": sprint.id,
            "project_id": sprint.project_id,
            "name": sprint.name,
            "goal": sprint.goal,
            "start_date": sprint.start_date,
            "end_date": sprint.end_date,
            "capacity_hours": sprint.capacity_hours,
            "status": sprint.status.value,
            "order": sprint.order,
            "stories": stories,
            "total_points": sum(s.story_points or 0 for s in sprint.stories),
            "total_hours": sum(s.estimated_hours or 0 for s in sprint.stories),
        })
    return result


@router.post("", response_model=SprintResponse)
def create_sprint(sprint: SprintCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == sprint.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    max_order = db.query(Sprint).filter(Sprint.project_id == sprint.project_id).count()

    db_sprint = Sprint(
        project_id=sprint.project_id,
        name=sprint.name,
        goal=sprint.goal,
        start_date=sprint.start_date,
        end_date=sprint.end_date,
        capacity_hours=sprint.capacity_hours,
        status=SprintStatus.PLANNING,
        order=max_order,
    )
    db.add(db_sprint)
    db.commit()
    db.refresh(db_sprint)

    return {
        "id": db_sprint.id,
        "project_id": db_sprint.project_id,
        "name": db_sprint.name,
        "goal": db_sprint.goal,
        "start_date": db_sprint.start_date,
        "end_date": db_sprint.end_date,
        "capacity_hours": db_sprint.capacity_hours,
        "status": db_sprint.status.value,
        "order": db_sprint.order,
        "stories": [],
    }


@router.patch("/{sprint_id}")
def update_sprint(sprint_id: int, update: SprintUpdate, db: Session = Depends(get_db)):
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    if update.name is not None:
        sprint.name = update.name
    if update.goal is not None:
        sprint.goal = update.goal
    if update.start_date is not None:
        sprint.start_date = update.start_date
    if update.end_date is not None:
        sprint.end_date = update.end_date
    if update.capacity_hours is not None:
        sprint.capacity_hours = update.capacity_hours
    if update.status is not None:
        sprint.status = SprintStatus(update.status)

    db.commit()
    db.refresh(sprint)
    return sprint


@router.post("/plan")
def plan_sprint(request: SprintPlanRequest, db: Session = Depends(get_db)):
    """Assign stories to a sprint."""
    sprint = db.query(Sprint).filter(Sprint.id == request.sprint_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    stories = db.query(Story).filter(Story.id.in_(request.story_ids)).all()
    for story in stories:
        story.sprint_id = request.sprint_id

    db.commit()
    return {"message": f"{len(stories)} stories assigned to sprint"}


@router.delete("/{sprint_id}")
def delete_sprint(sprint_id: int, db: Session = Depends(get_db)):
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    # Unassign stories from this sprint
    for story in sprint.stories:
        story.sprint_id = None

    db.delete(sprint)
    db.commit()
    return {"message": "Sprint deleted"}
