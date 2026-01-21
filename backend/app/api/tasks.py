from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models import Task
from app.models.task import TaskStatus

router = APIRouter()


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    estimated_hours: Optional[int] = None
    status: Optional[str] = None
    assigned_to_id: Optional[int] = None
    order: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    story_id: int
    title: str
    description: Optional[str]
    estimated_hours: Optional[int]
    status: str
    order: int

    class Config:
        from_attributes = True


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, update: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if update.title is not None:
        task.title = update.title
    if update.description is not None:
        task.description = update.description
    if update.estimated_hours is not None:
        task.estimated_hours = update.estimated_hours
    if update.status is not None:
        task.status = TaskStatus(update.status)
    if update.assigned_to_id is not None:
        task.assigned_to_id = update.assigned_to_id if update.assigned_to_id != 0 else None
    if update.order is not None:
        task.order = update.order

    db.commit()
    db.refresh(task)
    return {
        "id": task.id,
        "story_id": task.story_id,
        "title": task.title,
        "description": task.description,
        "estimated_hours": task.estimated_hours,
        "status": task.status.value,
        "order": task.order,
    }


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}
