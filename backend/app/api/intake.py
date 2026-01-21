from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json

from app.core.database import get_db
from app.models.intake import (
    Intake, PMBrief, ClarifyingQuestion, Artifact, IntakeStakeholder,
    IntakeSource, IntakeType, IntakeStatus
)
from app.services.intake_processor import process_intake, convert_to_project

router = APIRouter()


# ============ Request/Response Models ============

class IntakeCreate(BaseModel):
    title: str
    raw_content: str
    source: str = "manual"
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    source_author: Optional[str] = None
    source_channel: Optional[str] = None


class QuestionAnswer(BaseModel):
    answer: str
    answered_by: Optional[str] = None


class IntakeSummary(BaseModel):
    id: int
    title: str
    source: str
    inferred_type: Optional[str]
    type_confidence: Optional[float]
    priority_score: Optional[float]
    status: str
    received_at: datetime
    missing_info_count: int
    blocking_questions_count: int
    has_pm_brief: bool


class PMBriefResponse(BaseModel):
    problem_statement: Optional[str]
    target_users: list
    use_cases: list
    north_star_metric: Optional[str]
    input_metrics: list
    security_constraints: Optional[str]
    privacy_constraints: Optional[str]
    performance_constraints: Optional[str]
    budget_constraints: Optional[str]
    compatibility_constraints: Optional[str]
    assumptions: list
    out_of_scope: list
    acceptance_criteria: list
    team_dependencies: list
    service_dependencies: list
    vendor_dependencies: list
    missing_fields: list
    extraction_confidence: float


class QuestionResponse(BaseModel):
    id: int
    question: str
    context: Optional[str]
    target_field: Optional[str]
    assigned_to: Optional[str]
    priority: int
    is_blocking: bool
    is_answered: bool
    answer: Optional[str]


class StakeholderResponse(BaseModel):
    id: int
    name: str
    role: Optional[str]
    influence: str
    interest: str


class IntakeDetail(BaseModel):
    id: int
    title: str
    raw_content: str
    source: str
    source_url: Optional[str]
    source_author: Optional[str]
    inferred_type: Optional[str]
    type_confidence: Optional[float]
    priority_score: Optional[float]
    priority_rationale: Optional[str]
    status: str
    duplicate_of_id: Optional[int]
    duplicate_confidence: Optional[float]
    converted_to_project_id: Optional[int]
    received_at: datetime
    pm_brief: Optional[PMBriefResponse]
    clarifying_questions: list[QuestionResponse]
    stakeholders: list[StakeholderResponse]


# ============ Endpoints ============

@router.get("", response_model=list[IntakeSummary])
def list_intakes(
    status: Optional[str] = None,
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all intakes with optional filtering."""
    query = db.query(Intake)

    if status:
        query = query.filter(Intake.status == IntakeStatus(status))
    if source:
        query = query.filter(Intake.source == IntakeSource(source))

    intakes = query.order_by(Intake.received_at.desc()).all()

    return [
        IntakeSummary(
            id=i.id,
            title=i.title,
            source=i.source.value,
            inferred_type=i.inferred_type.value if i.inferred_type else None,
            type_confidence=i.type_confidence,
            priority_score=i.priority_score,
            status=i.status.value,
            received_at=i.received_at,
            missing_info_count=len(json.loads(i.pm_brief.missing_fields)) if i.pm_brief and i.pm_brief.missing_fields else 0,
            blocking_questions_count=sum(1 for q in i.clarifying_questions if q.is_blocking and not q.is_answered),
            has_pm_brief=i.pm_brief is not None
        )
        for i in intakes
    ]


@router.post("", response_model=IntakeSummary)
def create_intake(intake: IntakeCreate, db: Session = Depends(get_db)):
    """Create a new intake from any source."""
    try:
        source = IntakeSource(intake.source)
    except ValueError:
        source = IntakeSource.MANUAL

    db_intake = Intake(
        title=intake.title,
        raw_content=intake.raw_content,
        source=source,
        source_id=intake.source_id,
        source_url=intake.source_url,
        source_author=intake.source_author,
        source_channel=intake.source_channel,
        status=IntakeStatus.NEW
    )
    db.add(db_intake)
    db.commit()
    db.refresh(db_intake)

    return IntakeSummary(
        id=db_intake.id,
        title=db_intake.title,
        source=db_intake.source.value,
        inferred_type=None,
        type_confidence=None,
        priority_score=None,
        status=db_intake.status.value,
        received_at=db_intake.received_at,
        missing_info_count=0,
        blocking_questions_count=0,
        has_pm_brief=False
    )


@router.get("/{intake_id}", response_model=IntakeDetail)
def get_intake(intake_id: int, db: Session = Depends(get_db)):
    """Get detailed intake information."""
    intake = db.query(Intake).filter(Intake.id == intake_id).first()
    if not intake:
        raise HTTPException(status_code=404, detail="Intake not found")

    pm_brief = None
    if intake.pm_brief:
        b = intake.pm_brief
        pm_brief = PMBriefResponse(
            problem_statement=b.problem_statement,
            target_users=json.loads(b.target_users) if b.target_users else [],
            use_cases=json.loads(b.use_cases) if b.use_cases else [],
            north_star_metric=b.north_star_metric,
            input_metrics=json.loads(b.input_metrics) if b.input_metrics else [],
            security_constraints=b.security_constraints,
            privacy_constraints=b.privacy_constraints,
            performance_constraints=b.performance_constraints,
            budget_constraints=b.budget_constraints,
            compatibility_constraints=b.compatibility_constraints,
            assumptions=json.loads(b.assumptions) if b.assumptions else [],
            out_of_scope=json.loads(b.out_of_scope) if b.out_of_scope else [],
            acceptance_criteria=json.loads(b.acceptance_criteria) if b.acceptance_criteria else [],
            team_dependencies=json.loads(b.team_dependencies) if b.team_dependencies else [],
            service_dependencies=json.loads(b.service_dependencies) if b.service_dependencies else [],
            vendor_dependencies=json.loads(b.vendor_dependencies) if b.vendor_dependencies else [],
            missing_fields=json.loads(b.missing_fields) if b.missing_fields else [],
            extraction_confidence=b.extraction_confidence or 0.0
        )

    questions = [
        QuestionResponse(
            id=q.id,
            question=q.question,
            context=q.context,
            target_field=q.target_field,
            assigned_to=q.assigned_to,
            priority=q.priority,
            is_blocking=q.is_blocking,
            is_answered=q.is_answered,
            answer=q.answer
        )
        for q in sorted(intake.clarifying_questions, key=lambda x: x.priority)
    ]

    stakeholders = [
        StakeholderResponse(
            id=s.id,
            name=s.name,
            role=s.role,
            influence=s.influence,
            interest=s.interest
        )
        for s in intake.stakeholders
    ]

    return IntakeDetail(
        id=intake.id,
        title=intake.title,
        raw_content=intake.raw_content,
        source=intake.source.value,
        source_url=intake.source_url,
        source_author=intake.source_author,
        inferred_type=intake.inferred_type.value if intake.inferred_type else None,
        type_confidence=intake.type_confidence,
        priority_score=intake.priority_score,
        priority_rationale=intake.priority_rationale,
        status=intake.status.value,
        duplicate_of_id=intake.duplicate_of_id,
        duplicate_confidence=intake.duplicate_confidence,
        converted_to_project_id=intake.converted_to_project_id,
        received_at=intake.received_at,
        pm_brief=pm_brief,
        clarifying_questions=questions,
        stakeholders=stakeholders
    )


@router.post("/{intake_id}/process")
async def process_intake_endpoint(intake_id: int, db: Session = Depends(get_db)):
    """Process an intake: extract PM brief, detect duplicates, generate questions."""
    try:
        intake = await process_intake(db, intake_id)
        return {
            "message": "Intake processed successfully",
            "status": intake.status.value,
            "inferred_type": intake.inferred_type.value if intake.inferred_type else None,
            "priority_score": intake.priority_score
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{intake_id}/convert")
async def convert_intake_to_project(intake_id: int, db: Session = Depends(get_db)):
    """Convert a processed intake to a project."""
    try:
        project_id = await convert_to_project(db, intake_id)
        return {
            "message": "Intake converted to project",
            "project_id": project_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{intake_id}/questions/{question_id}/answer")
def answer_question(
    intake_id: int,
    question_id: int,
    answer: QuestionAnswer,
    db: Session = Depends(get_db)
):
    """Answer a clarifying question."""
    question = db.query(ClarifyingQuestion).filter(
        ClarifyingQuestion.id == question_id,
        ClarifyingQuestion.intake_id == intake_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question.answer = answer.answer
    question.answered_by = answer.answered_by
    question.answered_at = datetime.utcnow()
    question.is_answered = True

    # Check if all blocking questions are answered
    intake = db.query(Intake).filter(Intake.id == intake_id).first()
    blocking_unanswered = any(
        q.is_blocking and not q.is_answered
        for q in intake.clarifying_questions
    )

    if intake.status == IntakeStatus.NEEDS_CLARIFICATION and not blocking_unanswered:
        intake.status = IntakeStatus.READY

    db.commit()

    return {"message": "Question answered", "status": intake.status.value}


@router.patch("/{intake_id}/status")
def update_intake_status(
    intake_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Manually update intake status."""
    intake = db.query(Intake).filter(Intake.id == intake_id).first()
    if not intake:
        raise HTTPException(status_code=404, detail="Intake not found")

    try:
        intake.status = IntakeStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    db.commit()
    return {"message": "Status updated", "status": intake.status.value}


@router.post("/{intake_id}/merge/{duplicate_id}")
def merge_intakes(intake_id: int, duplicate_id: int, db: Session = Depends(get_db)):
    """Merge a duplicate intake into another."""
    intake = db.query(Intake).filter(Intake.id == intake_id).first()
    duplicate = db.query(Intake).filter(Intake.id == duplicate_id).first()

    if not intake or not duplicate:
        raise HTTPException(status_code=404, detail="Intake not found")

    # Mark duplicate
    duplicate.status = IntakeStatus.DUPLICATE
    duplicate.duplicate_of_id = intake_id
    duplicate.duplicate_confidence = 1.0

    # Append content as artifact
    artifact = Artifact(
        intake_id=intake_id,
        name=f"Merged from intake #{duplicate_id}",
        artifact_type="merged_request",
        content=f"Title: {duplicate.title}\n\n{duplicate.raw_content}"
    )
    db.add(artifact)
    db.commit()

    return {"message": f"Intake {duplicate_id} merged into {intake_id}"}


@router.delete("/{intake_id}")
def delete_intake(intake_id: int, db: Session = Depends(get_db)):
    """Delete an intake."""
    intake = db.query(Intake).filter(Intake.id == intake_id).first()
    if not intake:
        raise HTTPException(status_code=404, detail="Intake not found")

    db.delete(intake)
    db.commit()
    return {"message": "Intake deleted"}


# ============ Stats Endpoint ============

@router.get("/stats/summary")
def get_intake_stats(db: Session = Depends(get_db)):
    """Get intake statistics for dashboard."""
    total = db.query(Intake).count()
    by_status = {}
    for status in IntakeStatus:
        count = db.query(Intake).filter(Intake.status == status).count()
        by_status[status.value] = count

    by_type = {}
    for itype in IntakeType:
        count = db.query(Intake).filter(Intake.inferred_type == itype).count()
        by_type[itype.value] = count

    needs_attention = db.query(Intake).filter(
        Intake.status.in_([IntakeStatus.NEW, IntakeStatus.NEEDS_CLARIFICATION])
    ).count()

    return {
        "total": total,
        "by_status": by_status,
        "by_type": by_type,
        "needs_attention": needs_attention
    }
