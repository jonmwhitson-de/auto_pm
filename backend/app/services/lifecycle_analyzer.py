from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from app.services.llm import get_llm_provider
from app.models import (
    Project, OfferLifecyclePhase, ServiceTask,
    LifecyclePhase, PhaseStatus, ServiceTaskStatus, TaskSource,
    PHASE_ORDER
)
import json


# MCP Tool definitions for lifecycle analysis
LIFECYCLE_ANALYSIS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_offer_lifecycle_tasks",
            "description": "Generate a comprehensive Services-focused task checklist mapped to Offer Lifecycle phases from a PRD",
            "parameters": {
                "type": "object",
                "properties": {
                    "phases": {
                        "type": "array",
                        "description": "List of lifecycle phases with their tasks",
                        "items": {
                            "type": "object",
                            "properties": {
                                "phase": {
                                    "type": "string",
                                    "enum": ["concept", "define", "plan", "develop", "launch", "sustain"],
                                    "description": "The lifecycle phase"
                                },
                                "target_duration_days": {
                                    "type": "integer",
                                    "description": "Recommended duration for this phase in days"
                                },
                                "tasks": {
                                    "type": "array",
                                    "description": "Service tasks for this phase",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "title": {
                                                "type": "string",
                                                "description": "Task title"
                                            },
                                            "definition": {
                                                "type": "string",
                                                "description": "Detailed definition of what this task entails"
                                            },
                                            "category": {
                                                "type": "string",
                                                "enum": [
                                                    "Legal & Compliance",
                                                    "Finance & Pricing",
                                                    "Marketing & Communications",
                                                    "Sales Enablement",
                                                    "Product Management",
                                                    "Engineering & Technical",
                                                    "Operations & Support",
                                                    "Partner & Ecosystem",
                                                    "Training & Documentation",
                                                    "Quality & Certification"
                                                ],
                                                "description": "Task category"
                                            },
                                            "subcategory": {
                                                "type": "string",
                                                "description": "More specific subcategory"
                                            },
                                            "days_required": {
                                                "type": "integer",
                                                "description": "Estimated days to complete this task"
                                            },
                                            "owner_team": {
                                                "type": "string",
                                                "description": "Suggested team to own this task"
                                            },
                                            "is_required": {
                                                "type": "boolean",
                                                "description": "Whether this task is required or optional"
                                            },
                                            "confidence": {
                                                "type": "number",
                                                "description": "Confidence that this task is relevant (0-1)"
                                            },
                                            "reasoning": {
                                                "type": "string",
                                                "description": "Why this task was included"
                                            }
                                        },
                                        "required": ["title", "definition", "category", "days_required", "is_required"]
                                    }
                                }
                            },
                            "required": ["phase", "tasks"]
                        }
                    },
                    "offer_type": {
                        "type": "string",
                        "description": "Inferred type of offer (e.g., SaaS, Professional Services, Managed Service)"
                    },
                    "complexity_assessment": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "very_high"],
                        "description": "Overall complexity of the offer"
                    },
                    "total_estimated_days": {
                        "type": "integer",
                        "description": "Total estimated days from concept to launch"
                    },
                    "key_risks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key risks identified that could impact the lifecycle"
                    }
                },
                "required": ["phases", "offer_type", "complexity_assessment", "total_estimated_days"]
            }
        }
    }
]


LIFECYCLE_SYSTEM_PROMPT = """You are an expert Services Product Manager specializing in offer lifecycle management.
Your task is to analyze a Product Requirements Document (PRD) and generate a comprehensive checklist of
Services-focused tasks mapped to the Offer Lifecycle phases.

## Offer Lifecycle Phases (Sequential)
1. **CONCEPT** - Initial ideation, market analysis, business case development
2. **DEFINE** - Requirements definition, solution architecture, pricing strategy
3. **PLAN** - Detailed planning, resource allocation, go-to-market planning
4. **DEVELOP** - Build/configure, partner enablement, content creation
5. **LAUNCH** - Go-live activities, sales readiness, customer announcements
6. **SUSTAIN** - Ongoing operations, optimization, lifecycle management

## Task Generation Guidelines

For a typical enterprise Services offer, generate approximately 110 tasks total, distributed roughly as:
- CONCEPT: ~12-15 tasks (market analysis, competitive review, business case)
- DEFINE: ~20-25 tasks (requirements, architecture, pricing, contracts)
- PLAN: ~20-25 tasks (resource plans, GTM, enablement plans)
- DEVELOP: ~25-30 tasks (build, configure, partner work, content)
- LAUNCH: ~15-18 tasks (readiness, training, announcements)
- SUSTAIN: ~8-12 tasks (ops handoff, KPIs, feedback loops)

## Categories to Cover
For each phase, consider tasks across these categories:
- Legal & Compliance (contracts, terms, regulatory)
- Finance & Pricing (cost models, pricing, billing)
- Marketing & Communications (messaging, campaigns, collateral)
- Sales Enablement (training, playbooks, demos)
- Product Management (requirements, roadmap, features)
- Engineering & Technical (architecture, integration, security)
- Operations & Support (processes, SLAs, escalation)
- Partner & Ecosystem (certifications, enablement, contracts)
- Training & Documentation (internal, customer, partner)
- Quality & Certification (testing, compliance, audits)

## Date Calculation
- Estimate days_required for each task (typically 1-15 days)
- Tasks within a phase can run in parallel
- Phase duration should be sum of longest parallel track, not sum of all tasks
- Consider dependencies between tasks

## Services-Specific Focus
Focus on tasks relevant to bringing a SERVICE to market, not just software:
- Service delivery models
- Resource/staffing plans
- Partner delivery enablement
- Customer success handoffs
- Service level definitions
- Pricing and margin analysis
- Professional services scoping

Analyze the PRD carefully and generate relevant, actionable tasks. Be specific to the offering described.
If the PRD is thin on details, make reasonable assumptions for a Services organization.

Use the generate_offer_lifecycle_tasks tool to structure your analysis."""


async def analyze_lifecycle(
    db: Session,
    project_id: int,
    start_date: date | None = None
) -> list[OfferLifecyclePhase]:
    """Analyze a project's PRD and generate Offer Lifecycle phases and tasks."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Check if lifecycle already exists
    existing = db.query(OfferLifecyclePhase).filter(
        OfferLifecyclePhase.project_id == project_id
    ).first()
    if existing:
        raise ValueError("Lifecycle already exists for this project. Delete existing phases first.")

    # Use today if no start date provided
    if start_date is None:
        start_date = date.today()

    llm = get_llm_provider()
    messages = [
        {"role": "system", "content": LIFECYCLE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Analyze this PRD and generate the Offer Lifecycle task checklist:

Project: {project.name}
Description: {project.description or 'N/A'}

PRD Content:
{project.prd_content}

Generate a comprehensive Services-focused task checklist mapped to the 6 lifecycle phases.
Target approximately 110 tasks total, appropriately distributed across phases.
"""
        }
    ]

    _, tool_calls = await llm.complete_with_tools(messages, LIFECYCLE_ANALYSIS_TOOLS)

    created_phases = []
    if tool_calls:
        for tool_call in tool_calls:
            if tool_call["name"] == "generate_offer_lifecycle_tasks":
                data = json.loads(tool_call["arguments"])
                created_phases = _create_lifecycle_items(db, project, data, start_date)

    db.commit()
    return created_phases


def _create_lifecycle_items(
    db: Session,
    project: Project,
    data: dict,
    start_date: date
) -> list[OfferLifecyclePhase]:
    """Create database records from lifecycle analysis."""
    created_phases = []
    current_phase_start = start_date

    for phase_data in data.get("phases", []):
        phase_enum = LifecyclePhase(phase_data["phase"])
        phase_duration = phase_data.get("target_duration_days", 30)

        # Create phase
        phase = OfferLifecyclePhase(
            project_id=project.id,
            phase=phase_enum,
            status=PhaseStatus.NOT_STARTED,
            order=PHASE_ORDER[phase_enum],
            approval_required=True,
            target_start_date=current_phase_start,
            target_end_date=current_phase_start + timedelta(days=phase_duration)
        )
        db.add(phase)
        db.flush()  # Get the phase ID

        # Create tasks for this phase
        task_start = current_phase_start
        for task_order, task_data in enumerate(phase_data.get("tasks", [])):
            days_required = task_data.get("days_required", 5)

            task = ServiceTask(
                phase_id=phase.id,
                title=task_data["title"],
                definition=task_data.get("definition"),
                description=task_data.get("definition"),
                category=task_data.get("category"),
                subcategory=task_data.get("subcategory"),
                status=ServiceTaskStatus.NOT_STARTED,
                source=TaskSource.AI_GENERATED,
                target_start_date=task_start,
                target_complete_date=task_start + timedelta(days=days_required),
                days_required=days_required,
                team=task_data.get("owner_team"),
                order=task_order,
                is_required=task_data.get("is_required", True),
                ai_confidence=task_data.get("confidence"),
                ai_reasoning=task_data.get("reasoning")
            )
            db.add(task)

        created_phases.append(phase)
        # Next phase starts after this one
        current_phase_start = current_phase_start + timedelta(days=phase_duration)

    return created_phases


def initialize_lifecycle_phases(db: Session, project_id: int) -> list[OfferLifecyclePhase]:
    """Initialize empty lifecycle phases for a project (without tasks)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    phases = []
    for phase_enum, order in PHASE_ORDER.items():
        phase = OfferLifecyclePhase(
            project_id=project_id,
            phase=phase_enum,
            status=PhaseStatus.NOT_STARTED,
            order=order,
            approval_required=True
        )
        db.add(phase)
        phases.append(phase)

    db.commit()
    return phases


def approve_phase(
    db: Session,
    phase_id: int,
    approved_by: str,
    notes: str | None = None
) -> OfferLifecyclePhase:
    """Approve a phase to enable transition to the next phase."""
    phase = db.query(OfferLifecyclePhase).filter(OfferLifecyclePhase.id == phase_id).first()
    if not phase:
        raise ValueError(f"Phase {phase_id} not found")

    # Verify phase is ready for approval
    if phase.status != PhaseStatus.PENDING_APPROVAL:
        raise ValueError("Phase must be in PENDING_APPROVAL status to approve")

    phase.status = PhaseStatus.APPROVED
    phase.approved_by = approved_by
    phase.approved_at = datetime.utcnow()
    phase.approval_notes = notes
    phase.actual_end_date = date.today()

    # Auto-start next phase
    next_phase = db.query(OfferLifecyclePhase).filter(
        OfferLifecyclePhase.project_id == phase.project_id,
        OfferLifecyclePhase.order == phase.order + 1
    ).first()

    if next_phase and next_phase.status == PhaseStatus.NOT_STARTED:
        next_phase.status = PhaseStatus.IN_PROGRESS
        next_phase.actual_start_date = date.today()

    db.commit()
    db.refresh(phase)
    return phase


def override_phase_sequence(
    db: Session,
    phase_id: int,
    overridden_by: str,
    reason: str
) -> OfferLifecyclePhase:
    """Allow PM to override normal sequence and start a phase early."""
    phase = db.query(OfferLifecyclePhase).filter(OfferLifecyclePhase.id == phase_id).first()
    if not phase:
        raise ValueError(f"Phase {phase_id} not found")

    phase.sequence_overridden = True
    phase.override_reason = reason
    phase.overridden_by = overridden_by
    phase.overridden_at = datetime.utcnow()
    phase.status = PhaseStatus.IN_PROGRESS
    phase.actual_start_date = date.today()

    db.commit()
    db.refresh(phase)
    return phase


def delete_project_lifecycle(db: Session, project_id: int) -> bool:
    """Delete all lifecycle phases and tasks for a project."""
    phases = db.query(OfferLifecyclePhase).filter(
        OfferLifecyclePhase.project_id == project_id
    ).all()

    if not phases:
        return False

    for phase in phases:
        db.delete(phase)

    db.commit()
    return True


def get_lifecycle_stats(db: Session, project_id: int) -> dict:
    """Get lifecycle progress statistics for a project."""
    phases = db.query(OfferLifecyclePhase).filter(
        OfferLifecyclePhase.project_id == project_id
    ).order_by(OfferLifecyclePhase.order).all()

    if not phases:
        return None

    total_tasks = 0
    completed_tasks = 0
    current_phase = None

    for phase in phases:
        task_count = db.query(ServiceTask).filter(ServiceTask.phase_id == phase.id).count()
        completed_count = db.query(ServiceTask).filter(
            ServiceTask.phase_id == phase.id,
            ServiceTask.status == ServiceTaskStatus.COMPLETED
        ).count()
        total_tasks += task_count
        completed_tasks += completed_count

        if phase.status == PhaseStatus.IN_PROGRESS:
            current_phase = phase.phase.value

    return {
        "project_id": project_id,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overall_progress": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        "current_phase": current_phase,
        "estimated_completion_date": phases[-1].target_end_date if phases else None
    }
