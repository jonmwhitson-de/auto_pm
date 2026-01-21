from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models import Project
from app.services.prd_analyzer import analyze_prd

router = APIRouter()


class AnalyzeRequest(BaseModel):
    project_id: int


class AnalyzeResponse(BaseModel):
    message: str
    project_id: int


@router.post("", response_model=AnalyzeResponse)
async def analyze_project(request: AnalyzeRequest, db: Session = Depends(get_db)):
    """Analyze a project's PRD and generate work breakdown structure."""
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        await analyze_prd(db, request.project_id)
        return AnalyzeResponse(
            message="Analysis complete. Work breakdown has been generated.",
            project_id=request.project_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
