from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from docx import Document
import io

from app.core.database import get_db
from app.models import Project, Epic, Story, Task
from app.models.project import ProjectStatus

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    prd_content: str


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    prd_content: str
    status: ProjectStatus

    class Config:
        from_attributes = True


class ProjectWithBreakdown(ProjectResponse):
    epics: list
    total_story_points: int
    total_estimated_hours: int


@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()


@router.post("", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = Project(
        name=project.name,
        description=project.description,
        prd_content=project.prd_content,
        status=ProjectStatus.DRAFT,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.post("/upload", response_model=ProjectResponse)
async def create_project_from_file(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    content = await file.read()
    doc = Document(io.BytesIO(content))
    prd_content = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])

    db_project = Project(
        name=name,
        description=description,
        prd_content=prd_content,
        status=ProjectStatus.DRAFT,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/{project_id}", response_model=ProjectWithBreakdown)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    epics_data = []
    total_points = 0
    total_hours = 0

    for epic in project.epics:
        stories_data = []
        for story in epic.stories:
            tasks_data = [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "estimated_hours": task.estimated_hours,
                    "status": task.status.value,
                }
                for task in story.tasks
            ]
            stories_data.append(
                {
                    "id": story.id,
                    "title": story.title,
                    "description": story.description,
                    "acceptance_criteria": story.acceptance_criteria,
                    "story_points": story.story_points,
                    "estimated_hours": story.estimated_hours,
                    "priority": story.priority.value,
                    "status": story.status.value,
                    "sprint_id": story.sprint_id,
                    "tasks": tasks_data,
                }
            )
            if story.story_points:
                total_points += story.story_points
            if story.estimated_hours:
                total_hours += story.estimated_hours

        epics_data.append(
            {
                "id": epic.id,
                "title": epic.title,
                "description": epic.description,
                "priority": epic.priority.value,
                "stories": stories_data,
            }
        )

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "prd_content": project.prd_content,
        "status": project.status,
        "epics": epics_data,
        "total_story_points": total_points,
        "total_estimated_hours": total_hours,
    }


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}
