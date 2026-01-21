"""API endpoints for planning features: dependencies, decisions, assumptions, prioritization."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.models import (
    Project, Story,
    Dependency, DependencyType, DependencyStatus, ItemType,
    Decision, DecisionStatus,
    Assumption, AssumptionStatus, AssumptionRisk,
    StoryEstimate
)
from app.services.planning import (
    infer_dependencies,
    generate_range_estimates,
    extract_decisions_and_assumptions,
    update_story_prioritization,
    get_critical_path,
    calculate_rice_score,
    calculate_wsjf_score
)

router = APIRouter()


# ============ Pydantic Schemas ============

class DependencyCreate(BaseModel):
    source_type: str
    source_id: int
    target_type: str
    target_id: int
    dependency_type: str = "depends_on"
    notes: Optional[str] = None


class DependencyUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class DependencyResponse(BaseModel):
    id: int
    project_id: int
    source_type: str
    source_id: int
    target_type: str
    target_id: int
    dependency_type: str
    status: str
    inferred: bool
    confidence: Optional[float]
    inference_reason: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionCreate(BaseModel):
    title: str
    context: Optional[str] = None
    decision: str
    rationale: Optional[str] = None
    alternatives: Optional[list[str]] = None
    consequences: Optional[str] = None
    decision_maker: Optional[str] = None


class DecisionUpdate(BaseModel):
    title: Optional[str] = None
    context: Optional[str] = None
    decision: Optional[str] = None
    rationale: Optional[str] = None
    alternatives: Optional[list[str]] = None
    consequences: Optional[str] = None
    status: Optional[str] = None
    decision_maker: Optional[str] = None


class DecisionResponse(BaseModel):
    id: int
    project_id: int
    title: str
    context: Optional[str]
    decision: str
    rationale: Optional[str]
    alternatives: Optional[str]
    consequences: Optional[str]
    status: str
    decision_maker: Optional[str]
    decision_date: Optional[datetime]
    extracted_from: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AssumptionCreate(BaseModel):
    assumption: str
    context: Optional[str] = None
    impact_if_wrong: Optional[str] = None
    risk_level: str = "medium"
    validation_method: Optional[str] = None
    validation_owner: Optional[str] = None
    validation_deadline: Optional[datetime] = None


class AssumptionUpdate(BaseModel):
    assumption: Optional[str] = None
    context: Optional[str] = None
    impact_if_wrong: Optional[str] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
    validation_method: Optional[str] = None
    validation_owner: Optional[str] = None
    validation_deadline: Optional[datetime] = None
    validation_result: Optional[str] = None


class AssumptionResponse(BaseModel):
    id: int
    project_id: int
    assumption: str
    context: Optional[str]
    impact_if_wrong: Optional[str]
    status: str
    risk_level: str
    validation_method: Optional[str]
    validation_owner: Optional[str]
    validation_deadline: Optional[datetime]
    validation_result: Optional[str]
    validated_at: Optional[datetime]
    extracted_from: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RICEScores(BaseModel):
    reach: int
    impact: float
    confidence: float
    effort: float


class WSJFScores(BaseModel):
    business_value: int
    time_criticality: int
    risk_reduction: int
    job_size: int


class StoryEstimateResponse(BaseModel):
    id: int
    story_id: int
    estimate_p10: Optional[float]
    estimate_p50: Optional[float]
    estimate_p90: Optional[float]
    rice_score: Optional[float]
    wsjf_score: Optional[float]
    ai_estimate_p10: Optional[float]
    ai_estimate_p50: Optional[float]
    ai_estimate_p90: Optional[float]
    ai_confidence: Optional[float]
    ai_reasoning: Optional[str]

    class Config:
        from_attributes = True


class CriticalPathItem(BaseModel):
    item: str
    duration: float
    total_duration: float


# ============ Dependency Endpoints ============

@router.get("/projects/{project_id}/dependencies", response_model=list[DependencyResponse])
def list_dependencies(project_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    """List all dependencies for a project."""
    query = db.query(Dependency).filter(Dependency.project_id == project_id)
    if status:
        query = query.filter(Dependency.status == DependencyStatus(status))
    return query.all()


@router.post("/projects/{project_id}/dependencies", response_model=DependencyResponse)
def create_dependency(project_id: int, data: DependencyCreate, db: Session = Depends(get_db)):
    """Create a manual dependency."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    dep = Dependency(
        project_id=project_id,
        source_type=ItemType(data.source_type),
        source_id=data.source_id,
        target_type=ItemType(data.target_type),
        target_id=data.target_id,
        dependency_type=DependencyType(data.dependency_type),
        inferred=False,
        notes=data.notes
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


@router.put("/dependencies/{dependency_id}", response_model=DependencyResponse)
def update_dependency(dependency_id: int, data: DependencyUpdate, db: Session = Depends(get_db)):
    """Update a dependency."""
    dep = db.query(Dependency).filter(Dependency.id == dependency_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found")

    if data.status:
        dep.status = DependencyStatus(data.status)
    if data.notes is not None:
        dep.notes = data.notes

    db.commit()
    db.refresh(dep)
    return dep


@router.delete("/dependencies/{dependency_id}")
def delete_dependency(dependency_id: int, db: Session = Depends(get_db)):
    """Delete a dependency."""
    dep = db.query(Dependency).filter(Dependency.id == dependency_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found")

    db.delete(dep)
    db.commit()
    return {"status": "deleted"}


@router.post("/projects/{project_id}/dependencies/infer", response_model=list[DependencyResponse])
async def infer_project_dependencies(project_id: int, db: Session = Depends(get_db)):
    """Use AI to infer dependencies between work items."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    deps = await infer_dependencies(project_id, db)
    return deps


@router.get("/projects/{project_id}/critical-path", response_model=list[CriticalPathItem])
def get_project_critical_path(project_id: int, db: Session = Depends(get_db)):
    """Calculate and return the critical path for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return get_critical_path(project_id, db)


# ============ Decision Endpoints ============

@router.get("/projects/{project_id}/decisions", response_model=list[DecisionResponse])
def list_decisions(project_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    """List all decisions for a project."""
    query = db.query(Decision).filter(Decision.project_id == project_id)
    if status:
        query = query.filter(Decision.status == DecisionStatus(status))
    return query.order_by(Decision.created_at.desc()).all()


@router.post("/projects/{project_id}/decisions", response_model=DecisionResponse)
def create_decision(project_id: int, data: DecisionCreate, db: Session = Depends(get_db)):
    """Create a new decision."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    import json
    decision = Decision(
        project_id=project_id,
        title=data.title,
        context=data.context,
        decision=data.decision,
        rationale=data.rationale,
        alternatives=json.dumps(data.alternatives) if data.alternatives else None,
        consequences=data.consequences,
        decision_maker=data.decision_maker
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


@router.put("/decisions/{decision_id}", response_model=DecisionResponse)
def update_decision(decision_id: int, data: DecisionUpdate, db: Session = Depends(get_db)):
    """Update a decision."""
    import json
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    if data.title:
        decision.title = data.title
    if data.context is not None:
        decision.context = data.context
    if data.decision:
        decision.decision = data.decision
    if data.rationale is not None:
        decision.rationale = data.rationale
    if data.alternatives is not None:
        decision.alternatives = json.dumps(data.alternatives)
    if data.consequences is not None:
        decision.consequences = data.consequences
    if data.status:
        decision.status = DecisionStatus(data.status)
        if data.status == "accepted":
            decision.decision_date = datetime.utcnow()
    if data.decision_maker is not None:
        decision.decision_maker = data.decision_maker

    db.commit()
    db.refresh(decision)
    return decision


@router.delete("/decisions/{decision_id}")
def delete_decision(decision_id: int, db: Session = Depends(get_db)):
    """Delete a decision."""
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    db.delete(decision)
    db.commit()
    return {"status": "deleted"}


# ============ Assumption Endpoints ============

@router.get("/projects/{project_id}/assumptions", response_model=list[AssumptionResponse])
def list_assumptions(
    project_id: int,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all assumptions for a project."""
    query = db.query(Assumption).filter(Assumption.project_id == project_id)
    if status:
        query = query.filter(Assumption.status == AssumptionStatus(status))
    if risk_level:
        query = query.filter(Assumption.risk_level == AssumptionRisk(risk_level))
    return query.order_by(Assumption.risk_level.desc(), Assumption.created_at.desc()).all()


@router.post("/projects/{project_id}/assumptions", response_model=AssumptionResponse)
def create_assumption(project_id: int, data: AssumptionCreate, db: Session = Depends(get_db)):
    """Create a new assumption."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    assumption = Assumption(
        project_id=project_id,
        assumption=data.assumption,
        context=data.context,
        impact_if_wrong=data.impact_if_wrong,
        risk_level=AssumptionRisk(data.risk_level),
        validation_method=data.validation_method,
        validation_owner=data.validation_owner,
        validation_deadline=data.validation_deadline
    )
    db.add(assumption)
    db.commit()
    db.refresh(assumption)
    return assumption


@router.put("/assumptions/{assumption_id}", response_model=AssumptionResponse)
def update_assumption(assumption_id: int, data: AssumptionUpdate, db: Session = Depends(get_db)):
    """Update an assumption."""
    assumption = db.query(Assumption).filter(Assumption.id == assumption_id).first()
    if not assumption:
        raise HTTPException(status_code=404, detail="Assumption not found")

    if data.assumption:
        assumption.assumption = data.assumption
    if data.context is not None:
        assumption.context = data.context
    if data.impact_if_wrong is not None:
        assumption.impact_if_wrong = data.impact_if_wrong
    if data.status:
        assumption.status = AssumptionStatus(data.status)
        if data.status in ["validated", "invalidated"]:
            assumption.validated_at = datetime.utcnow()
    if data.risk_level:
        assumption.risk_level = AssumptionRisk(data.risk_level)
    if data.validation_method is not None:
        assumption.validation_method = data.validation_method
    if data.validation_owner is not None:
        assumption.validation_owner = data.validation_owner
    if data.validation_deadline is not None:
        assumption.validation_deadline = data.validation_deadline
    if data.validation_result is not None:
        assumption.validation_result = data.validation_result

    db.commit()
    db.refresh(assumption)
    return assumption


@router.delete("/assumptions/{assumption_id}")
def delete_assumption(assumption_id: int, db: Session = Depends(get_db)):
    """Delete an assumption."""
    assumption = db.query(Assumption).filter(Assumption.id == assumption_id).first()
    if not assumption:
        raise HTTPException(status_code=404, detail="Assumption not found")

    db.delete(assumption)
    db.commit()
    return {"status": "deleted"}


# ============ Extraction Endpoint ============

class ExtractRequest(BaseModel):
    content: str
    source: str = "manual"


@router.post("/projects/{project_id}/extract-planning")
async def extract_planning_items(project_id: int, data: ExtractRequest, db: Session = Depends(get_db)):
    """Extract decisions and assumptions from text content using AI."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    decisions, assumptions = await extract_decisions_and_assumptions(
        project_id, data.content, data.source, db
    )

    return {
        "decisions_extracted": len(decisions),
        "assumptions_extracted": len(assumptions),
        "decisions": [DecisionResponse.model_validate(d) for d in decisions],
        "assumptions": [AssumptionResponse.model_validate(a) for a in assumptions]
    }


# ============ Estimation & Prioritization Endpoints ============

@router.get("/stories/{story_id}/estimate", response_model=StoryEstimateResponse)
def get_story_estimate(story_id: int, db: Session = Depends(get_db)):
    """Get estimate and prioritization data for a story."""
    estimate = db.query(StoryEstimate).filter(StoryEstimate.story_id == story_id).first()
    if not estimate:
        raise HTTPException(status_code=404, detail="No estimate found for this story")
    return estimate


@router.post("/stories/{story_id}/estimate/generate", response_model=StoryEstimateResponse)
async def generate_story_estimate(story_id: int, db: Session = Depends(get_db)):
    """Generate AI-powered range estimates for a story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    estimate = await generate_range_estimates(story_id, db)
    return estimate


@router.put("/stories/{story_id}/estimate/rice", response_model=StoryEstimateResponse)
def set_rice_scores(story_id: int, scores: RICEScores, db: Session = Depends(get_db)):
    """Set RICE prioritization scores for a story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    estimate = update_story_prioritization(
        story_id,
        "rice",
        scores.model_dump(),
        db
    )
    return estimate


@router.put("/stories/{story_id}/estimate/wsjf", response_model=StoryEstimateResponse)
def set_wsjf_scores(story_id: int, scores: WSJFScores, db: Session = Depends(get_db)):
    """Set WSJF prioritization scores for a story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    estimate = update_story_prioritization(
        story_id,
        "wsjf",
        scores.model_dump(),
        db
    )
    return estimate


class ManualEstimate(BaseModel):
    p10: float
    p50: float
    p90: float


@router.put("/stories/{story_id}/estimate/range", response_model=StoryEstimateResponse)
def set_range_estimate(story_id: int, data: ManualEstimate, db: Session = Depends(get_db)):
    """Set manual range estimates for a story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    estimate = db.query(StoryEstimate).filter(StoryEstimate.story_id == story_id).first()
    if not estimate:
        estimate = StoryEstimate(story_id=story_id)
        db.add(estimate)

    estimate.estimate_p10 = data.p10
    estimate.estimate_p50 = data.p50
    estimate.estimate_p90 = data.p90

    db.commit()
    db.refresh(estimate)
    return estimate


# ============ Prioritized Backlog View ============

class PrioritizedStory(BaseModel):
    id: int
    title: str
    epic_id: int
    story_points: Optional[int]
    estimated_hours: Optional[int]
    rice_score: Optional[float]
    wsjf_score: Optional[float]
    estimate_p50: Optional[float]

    class Config:
        from_attributes = True


@router.get("/projects/{project_id}/prioritized-backlog")
def get_prioritized_backlog(
    project_id: int,
    model: str = "rice",
    db: Session = Depends(get_db)
):
    """Get backlog sorted by prioritization score."""
    from app.models import Epic

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all stories with estimates
    epics = db.query(Epic).filter(Epic.project_id == project_id).all()
    stories_data = []

    for epic in epics:
        stories = db.query(Story).filter(Story.epic_id == epic.id).all()
        for story in stories:
            estimate = db.query(StoryEstimate).filter(StoryEstimate.story_id == story.id).first()
            score = None
            if estimate:
                score = estimate.rice_score if model == "rice" else estimate.wsjf_score

            stories_data.append({
                "id": story.id,
                "title": story.title,
                "epic_id": epic.id,
                "epic_title": epic.title,
                "story_points": story.story_points,
                "estimated_hours": story.estimated_hours,
                "rice_score": estimate.rice_score if estimate else None,
                "wsjf_score": estimate.wsjf_score if estimate else None,
                "estimate_p50": estimate.estimate_p50 if estimate else None,
                "priority_score": score
            })

    # Sort by prioritization score (descending)
    stories_data.sort(key=lambda x: x["priority_score"] or 0, reverse=True)

    return {"model": model, "stories": stories_data}
