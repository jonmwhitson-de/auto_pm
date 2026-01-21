from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime, timedelta
from app.core.database import get_db
from app.models import (
    Project, OfferLifecyclePhase, ServiceTask,
    LifecyclePhase, PhaseStatus, ServiceTaskStatus, TaskSource
)
from app.services.lifecycle_analyzer import (
    analyze_lifecycle, initialize_lifecycle_phases,
    approve_phase, override_phase_sequence, delete_project_lifecycle
)

router = APIRouter()


# ============ Pydantic Schemas ============

class LifecycleAnalyzeRequest(BaseModel):
    project_id: int
    start_date: Optional[date] = None


class PhaseResponse(BaseModel):
    id: int
    project_id: int
    phase: str
    status: str
    order: int
    approval_required: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    sequence_overridden: bool
    override_reason: Optional[str] = None
    target_start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    task_count: int
    completed_task_count: int

    class Config:
        from_attributes = True


class ServiceTaskResponse(BaseModel):
    id: int
    phase_id: int
    title: str
    description: Optional[str] = None
    definition: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    status: str
    source: str
    target_start_date: Optional[date] = None
    target_complete_date: Optional[date] = None
    days_required: Optional[int] = None
    actual_start_date: Optional[date] = None
    actual_complete_date: Optional[date] = None
    owner: Optional[str] = None
    team: Optional[str] = None
    linked_epic_id: Optional[int] = None
    linked_story_id: Optional[int] = None
    order: int
    is_required: bool
    notes: Optional[str] = None
    completion_notes: Optional[str] = None

    class Config:
        from_attributes = True


class ServiceTaskCreate(BaseModel):
    title: str
    definition: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    days_required: Optional[int] = None
    target_start_date: Optional[date] = None
    owner: Optional[str] = None
    team: Optional[str] = None
    is_required: bool = True


class ServiceTaskUpdate(BaseModel):
    title: Optional[str] = None
    definition: Optional[str] = None
    status: Optional[str] = None
    target_start_date: Optional[date] = None
    target_complete_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_complete_date: Optional[date] = None
    owner: Optional[str] = None
    team: Optional[str] = None
    notes: Optional[str] = None
    completion_notes: Optional[str] = None
    linked_epic_id: Optional[int] = None
    linked_story_id: Optional[int] = None


class PhaseApprovalRequest(BaseModel):
    approved_by: str
    notes: Optional[str] = None


class PhaseOverrideRequest(BaseModel):
    overridden_by: str
    reason: str


class LifecycleSummary(BaseModel):
    project_id: int
    total_tasks: int
    completed_tasks: int
    phases: list[PhaseResponse]
    current_phase: Optional[str] = None
    overall_progress: float
    estimated_completion_date: Optional[date] = None


# ============ Lifecycle Endpoints ============

@router.post("/analyze", response_model=list[PhaseResponse])
async def analyze_project_lifecycle(
    request: LifecycleAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """Analyze PRD and generate Offer Lifecycle phases and tasks."""
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if lifecycle already exists
    existing = db.query(OfferLifecyclePhase).filter(
        OfferLifecyclePhase.project_id == request.project_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Lifecycle already exists for this project. Delete first to regenerate."
        )

    try:
        phases = await analyze_lifecycle(db, request.project_id, request.start_date)
        return _build_phase_responses(db, phases)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}", response_model=LifecycleSummary)
def get_project_lifecycle(project_id: int, db: Session = Depends(get_db)):
    """Get full lifecycle summary for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    phases = db.query(OfferLifecyclePhase).filter(
        OfferLifecyclePhase.project_id == project_id
    ).order_by(OfferLifecyclePhase.order).all()

    if not phases:
        raise HTTPException(status_code=404, detail="No lifecycle found for this project")

    phase_responses = _build_phase_responses(db, phases)

    total_tasks = sum(p.task_count for p in phase_responses)
    completed_tasks = sum(p.completed_task_count for p in phase_responses)

    current_phase = None
    for p in phase_responses:
        if p.status == "in_progress":
            current_phase = p.phase
            break

    return LifecycleSummary(
        project_id=project_id,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        phases=phase_responses,
        current_phase=current_phase,
        overall_progress=(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        estimated_completion_date=phases[-1].target_end_date if phases else None
    )


@router.delete("/projects/{project_id}")
def delete_lifecycle(project_id: int, db: Session = Depends(get_db)):
    """Delete all lifecycle phases and tasks for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    deleted = delete_project_lifecycle(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="No lifecycle found for this project")

    return {"status": "deleted"}


@router.get("/phases/{phase_id}", response_model=PhaseResponse)
def get_phase(phase_id: int, db: Session = Depends(get_db)):
    """Get a specific lifecycle phase."""
    phase = db.query(OfferLifecyclePhase).filter(OfferLifecyclePhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    return _build_phase_response(db, phase)


@router.post("/phases/{phase_id}/start", response_model=PhaseResponse)
def start_phase(phase_id: int, db: Session = Depends(get_db)):
    """Start a phase (transition from NOT_STARTED to IN_PROGRESS)."""
    phase = db.query(OfferLifecyclePhase).filter(OfferLifecyclePhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    # Check if previous phase is approved (unless this is CONCEPT or override)
    if phase.order > 1 and not phase.sequence_overridden:
        prev_phase = db.query(OfferLifecyclePhase).filter(
            OfferLifecyclePhase.project_id == phase.project_id,
            OfferLifecyclePhase.order == phase.order - 1
        ).first()
        if prev_phase and prev_phase.status != PhaseStatus.APPROVED:
            raise HTTPException(
                status_code=400,
                detail="Previous phase must be approved before starting this phase"
            )

    phase.status = PhaseStatus.IN_PROGRESS
    phase.actual_start_date = date.today()
    db.commit()
    db.refresh(phase)
    return _build_phase_response(db, phase)


@router.post("/phases/{phase_id}/submit-for-approval", response_model=PhaseResponse)
def submit_phase_for_approval(phase_id: int, db: Session = Depends(get_db)):
    """Submit a phase for approval."""
    phase = db.query(OfferLifecyclePhase).filter(OfferLifecyclePhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    if phase.status != PhaseStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=400,
            detail="Phase must be IN_PROGRESS to submit for approval"
        )

    phase.status = PhaseStatus.PENDING_APPROVAL
    db.commit()
    db.refresh(phase)
    return _build_phase_response(db, phase)


@router.post("/phases/{phase_id}/approve", response_model=PhaseResponse)
def approve_phase_endpoint(
    phase_id: int,
    request: PhaseApprovalRequest,
    db: Session = Depends(get_db)
):
    """Approve a phase and optionally start the next phase."""
    try:
        phase = approve_phase(db, phase_id, request.approved_by, request.notes)
        return _build_phase_response(db, phase)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/phases/{phase_id}/override", response_model=PhaseResponse)
def override_phase_endpoint(
    phase_id: int,
    request: PhaseOverrideRequest,
    db: Session = Depends(get_db)
):
    """Override normal sequence and start a phase early."""
    try:
        phase = override_phase_sequence(db, phase_id, request.overridden_by, request.reason)
        return _build_phase_response(db, phase)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Service Task Endpoints ============

@router.get("/phases/{phase_id}/tasks", response_model=list[ServiceTaskResponse])
def list_phase_tasks(
    phase_id: int,
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all tasks for a phase."""
    phase = db.query(OfferLifecyclePhase).filter(OfferLifecyclePhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    query = db.query(ServiceTask).filter(ServiceTask.phase_id == phase_id)
    if status:
        query = query.filter(ServiceTask.status == ServiceTaskStatus(status))
    if category:
        query = query.filter(ServiceTask.category == category)
    return query.order_by(ServiceTask.order).all()


@router.post("/phases/{phase_id}/tasks", response_model=ServiceTaskResponse)
def create_task(
    phase_id: int,
    data: ServiceTaskCreate,
    db: Session = Depends(get_db)
):
    """Create a new service task (manual addition)."""
    phase = db.query(OfferLifecyclePhase).filter(OfferLifecyclePhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    max_order = db.query(func.max(ServiceTask.order)).filter(
        ServiceTask.phase_id == phase_id
    ).scalar() or 0

    task = ServiceTask(
        phase_id=phase_id,
        title=data.title,
        definition=data.definition,
        description=data.definition,
        category=data.category,
        subcategory=data.subcategory,
        days_required=data.days_required,
        target_start_date=data.target_start_date,
        owner=data.owner,
        team=data.team,
        is_required=data.is_required,
        source=TaskSource.MANUAL,
        status=ServiceTaskStatus.NOT_STARTED,
        order=max_order + 1
    )

    # Calculate target complete date if we have start date and days
    if data.target_start_date and data.days_required:
        task.target_complete_date = data.target_start_date + timedelta(days=data.days_required)

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks/{task_id}", response_model=ServiceTaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific service task."""
    task = db.query(ServiceTask).filter(ServiceTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/tasks/{task_id}", response_model=ServiceTaskResponse)
def update_task(
    task_id: int,
    data: ServiceTaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a service task."""
    task = db.query(ServiceTask).filter(ServiceTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = data.model_dump(exclude_unset=True)

    # Handle status transitions
    if "status" in update_data:
        new_status = ServiceTaskStatus(update_data["status"])
        if new_status == ServiceTaskStatus.COMPLETED and task.status != ServiceTaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
            if not task.actual_complete_date:
                task.actual_complete_date = date.today()
        elif new_status == ServiceTaskStatus.IN_PROGRESS and task.status == ServiceTaskStatus.NOT_STARTED:
            if not task.actual_start_date:
                task.actual_start_date = date.today()
        task.status = new_status
        del update_data["status"]

    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a service task."""
    task = db.query(ServiceTask).filter(ServiceTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"status": "deleted"}


@router.post("/tasks/{task_id}/link-dev-work", response_model=ServiceTaskResponse)
def link_task_to_dev_work(
    task_id: int,
    epic_id: Optional[int] = None,
    story_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Link a service task to development work (epic or story)."""
    task = db.query(ServiceTask).filter(ServiceTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if epic_id is not None:
        task.linked_epic_id = epic_id
    if story_id is not None:
        task.linked_story_id = story_id

    db.commit()
    db.refresh(task)
    return task


# ============ Bulk Operations ============

@router.post("/phases/{phase_id}/tasks/bulk-status")
def bulk_update_task_status(
    phase_id: int,
    task_ids: list[int],
    status: str,
    db: Session = Depends(get_db)
):
    """Update status for multiple tasks at once."""
    phase = db.query(OfferLifecyclePhase).filter(OfferLifecyclePhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    new_status = ServiceTaskStatus(status)
    updated = 0

    for task_id in task_ids:
        task = db.query(ServiceTask).filter(
            ServiceTask.id == task_id,
            ServiceTask.phase_id == phase_id
        ).first()
        if task:
            if new_status == ServiceTaskStatus.COMPLETED and task.status != ServiceTaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
                task.actual_complete_date = date.today()
            elif new_status == ServiceTaskStatus.IN_PROGRESS and task.status == ServiceTaskStatus.NOT_STARTED:
                task.actual_start_date = date.today()
            task.status = new_status
            updated += 1

    db.commit()
    return {"updated": updated}


# ============ Helper Functions ============

def _build_phase_response(db: Session, phase: OfferLifecyclePhase) -> PhaseResponse:
    """Build a phase response with task counts."""
    task_count = db.query(ServiceTask).filter(ServiceTask.phase_id == phase.id).count()
    completed_count = db.query(ServiceTask).filter(
        ServiceTask.phase_id == phase.id,
        ServiceTask.status == ServiceTaskStatus.COMPLETED
    ).count()

    return PhaseResponse(
        id=phase.id,
        project_id=phase.project_id,
        phase=phase.phase.value,
        status=phase.status.value if phase.status else "not_started",
        order=phase.order,
        approval_required=phase.approval_required if phase.approval_required is not None else True,
        approved_by=phase.approved_by,
        approved_at=phase.approved_at,
        approval_notes=phase.approval_notes,
        sequence_overridden=phase.sequence_overridden if phase.sequence_overridden is not None else False,
        override_reason=phase.override_reason,
        target_start_date=phase.target_start_date,
        target_end_date=phase.target_end_date,
        actual_start_date=phase.actual_start_date,
        actual_end_date=phase.actual_end_date,
        task_count=task_count,
        completed_task_count=completed_count
    )


def _build_phase_responses(db: Session, phases: list[OfferLifecyclePhase]) -> list[PhaseResponse]:
    """Build phase responses for multiple phases."""
    return [_build_phase_response(db, p) for p in phases]
