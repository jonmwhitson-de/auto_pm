from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models import TeamMember, Project

router = APIRouter()


class TeamMemberCreate(BaseModel):
    project_id: int
    name: str
    email: Optional[str] = None
    role: Optional[str] = None
    hours_per_sprint: int = 40


class TeamMemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    hours_per_sprint: Optional[int] = None


class TeamMemberResponse(BaseModel):
    id: int
    project_id: int
    name: str
    email: Optional[str]
    role: Optional[str]
    hours_per_sprint: int

    class Config:
        from_attributes = True


@router.get("/project/{project_id}", response_model=list[TeamMemberResponse])
def list_team_members(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.team_members


@router.post("", response_model=TeamMemberResponse)
def create_team_member(member: TeamMemberCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == member.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_member = TeamMember(
        project_id=member.project_id,
        name=member.name,
        email=member.email,
        role=member.role,
        hours_per_sprint=member.hours_per_sprint,
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@router.patch("/{member_id}", response_model=TeamMemberResponse)
def update_team_member(member_id: int, update: TeamMemberUpdate, db: Session = Depends(get_db)):
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")

    if update.name is not None:
        member.name = update.name
    if update.email is not None:
        member.email = update.email
    if update.role is not None:
        member.role = update.role
    if update.hours_per_sprint is not None:
        member.hours_per_sprint = update.hours_per_sprint

    db.commit()
    db.refresh(member)
    return member


@router.delete("/{member_id}")
def delete_team_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    db.delete(member)
    db.commit()
    return {"message": "Team member deleted"}


@router.get("/project/{project_id}/capacity")
def get_team_capacity(project_id: int, db: Session = Depends(get_db)):
    """Get total team capacity for sprint planning."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    total_hours = sum(m.hours_per_sprint for m in project.team_members)
    return {
        "team_size": len(project.team_members),
        "total_hours_per_sprint": total_hours,
        "members": [
            {"id": m.id, "name": m.name, "hours": m.hours_per_sprint}
            for m in project.team_members
        ],
    }
