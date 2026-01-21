from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models import Epic
from app.models.epic import Priority

router = APIRouter()


class EpicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    order: Optional[int] = None


class EpicResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str]
    priority: str
    order: int

    class Config:
        from_attributes = True


@router.get("/{epic_id}")
def get_epic(epic_id: int, db: Session = Depends(get_db)):
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    return epic


@router.patch("/{epic_id}", response_model=EpicResponse)
def update_epic(epic_id: int, update: EpicUpdate, db: Session = Depends(get_db)):
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    if update.title is not None:
        epic.title = update.title
    if update.description is not None:
        epic.description = update.description
    if update.priority is not None:
        epic.priority = Priority(update.priority)
    if update.order is not None:
        epic.order = update.order

    db.commit()
    db.refresh(epic)
    return {
        "id": epic.id,
        "project_id": epic.project_id,
        "title": epic.title,
        "description": epic.description,
        "priority": epic.priority.value,
        "order": epic.order,
    }


@router.delete("/{epic_id}")
def delete_epic(epic_id: int, db: Session = Depends(get_db)):
    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    db.delete(epic)
    db.commit()
    return {"message": "Epic deleted"}
