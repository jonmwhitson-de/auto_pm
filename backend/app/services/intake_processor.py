"""Service for processing intakes: extraction, classification, duplicate detection, and clarifying questions."""
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from app.services.llm import get_llm_provider
from app.models.intake import (
    Intake, PMBrief, ClarifyingQuestion, IntakeStakeholder,
    IntakeStatus, IntakeType, IntakeSource
)
import json

# MCP Tool definitions for intake processing
INTAKE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "extract_pm_brief",
            "description": "Extract a structured PM brief from raw intake content",
            "parameters": {
                "type": "object",
                "properties": {
                    "inferred_type": {
                        "type": "string",
                        "enum": ["bug", "feature", "tech_debt", "risk", "compliance", "enhancement", "unknown"],
                        "description": "The type of request"
                    },
                    "type_confidence": {
                        "type": "number",
                        "description": "Confidence in the type classification (0-1)"
                    },
                    "priority_score": {
                        "type": "number",
                        "description": "Priority score from 0-100 based on urgency, impact, and strategic alignment"
                    },
                    "priority_rationale": {
                        "type": "string",
                        "description": "Explanation of the priority score"
                    },
                    "problem_statement": {
                        "type": "string",
                        "description": "Clear statement of the problem to be solved"
                    },
                    "target_users": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of target user types/personas"
                    },
                    "use_cases": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific use cases this addresses"
                    },
                    "north_star_metric": {
                        "type": "string",
                        "description": "Primary success metric"
                    },
                    "input_metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Supporting/input metrics"
                    },
                    "security_constraints": {
                        "type": "string",
                        "description": "Security requirements or constraints"
                    },
                    "privacy_constraints": {
                        "type": "string",
                        "description": "Privacy/data handling requirements"
                    },
                    "performance_constraints": {
                        "type": "string",
                        "description": "Latency, throughput, or other performance requirements"
                    },
                    "budget_constraints": {
                        "type": "string",
                        "description": "Budget or resource constraints"
                    },
                    "compatibility_constraints": {
                        "type": "string",
                        "description": "Compatibility requirements with existing systems"
                    },
                    "assumptions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Explicit assumptions being made"
                    },
                    "out_of_scope": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Items explicitly out of scope"
                    },
                    "acceptance_criteria": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Testable acceptance criteria"
                    },
                    "team_dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Teams this depends on"
                    },
                    "service_dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Services/systems this depends on"
                    },
                    "vendor_dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "External vendors this depends on"
                    },
                    "stakeholders": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "role": {"type": "string", "enum": ["decision_maker", "contributor", "informed"]},
                                "influence": {"type": "string", "enum": ["low", "medium", "high"]},
                                "interest": {"type": "string", "enum": ["low", "medium", "high"]}
                            }
                        },
                        "description": "Identified stakeholders"
                    },
                    "missing_fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields that couldn't be extracted and need clarification"
                    },
                    "extraction_confidence": {
                        "type": "number",
                        "description": "Overall confidence in the extraction (0-1)"
                    }
                },
                "required": ["inferred_type", "problem_statement", "missing_fields", "extraction_confidence"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_clarifying_questions",
            "description": "Generate questions to reduce ambiguity in the intake",
            "parameters": {
                "type": "object",
                "properties": {
                    "questions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {"type": "string", "description": "The clarifying question"},
                                "context": {"type": "string", "description": "Why this question matters for reducing ambiguity"},
                                "target_field": {"type": "string", "description": "Which PM brief field this clarifies"},
                                "priority": {"type": "integer", "description": "Priority 1-5, where 1 is highest ambiguity reduction"},
                                "suggested_assignee": {"type": "string", "description": "Who should answer this (role or name if mentioned)"},
                                "is_blocking": {"type": "boolean", "description": "Whether this blocks further progress"}
                            },
                            "required": ["question", "context", "target_field", "priority", "is_blocking"]
                        },
                        "description": "List of clarifying questions, ordered by impact on reducing ambiguity"
                    }
                },
                "required": ["questions"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_duplicate",
            "description": "Check if this intake is a duplicate of existing ones",
            "parameters": {
                "type": "object",
                "properties": {
                    "is_duplicate": {"type": "boolean"},
                    "duplicate_of_id": {"type": "integer", "description": "ID of the duplicate intake if found"},
                    "confidence": {"type": "number", "description": "Confidence that this is a duplicate (0-1)"},
                    "evidence": {"type": "string", "description": "Explanation of why this appears to be a duplicate"}
                },
                "required": ["is_duplicate", "confidence"]
            }
        }
    }
]

EXTRACTION_SYSTEM_PROMPT = """You are an expert product manager. Your task is to analyze incoming requests and extract structured information.

Given raw content from various sources (Slack, email, meeting transcripts, support tickets, etc.), you must:

1. Classify the request type (bug, feature, tech debt, risk, compliance, enhancement)
2. Extract all available information into a structured PM brief
3. Identify what information is missing
4. Assign a priority score based on:
   - Business impact
   - Urgency indicators
   - Strategic alignment
   - Risk if not addressed

Be thorough but realistic - mark confidence levels honestly. If information is ambiguous or missing, flag it.

Use the extract_pm_brief tool to structure your analysis."""

CLARIFICATION_SYSTEM_PROMPT = """You are an expert product manager focused on reducing ambiguity.

Given an intake and its extracted PM brief, generate clarifying questions that:
1. Target the highest-impact ambiguities first
2. Are specific and actionable (not vague)
3. Can be answered by a specific person/role
4. Will materially improve the quality of the requirements

Only ask questions that will significantly reduce ambiguity. Don't ask for nice-to-haves.

Mark questions as blocking if they prevent meaningful progress on scoping.

Use the generate_clarifying_questions tool."""

DUPLICATE_SYSTEM_PROMPT = """You are analyzing whether a new intake is a duplicate of existing ones.

Consider an intake a duplicate if:
- It describes the same problem/feature from a different angle
- It's a follow-up or re-request of the same thing
- The scope significantly overlaps (>70%)

Do NOT mark as duplicate if:
- It's related but addresses different aspects
- It's an evolution or extension of previous work
- The overlap is incidental

Provide evidence for your decision.

Use the check_duplicate tool."""


async def process_intake(db: Session, intake_id: int) -> Intake:
    """Process an intake: extract PM brief, detect duplicates, generate questions."""
    intake = db.query(Intake).filter(Intake.id == intake_id).first()
    if not intake:
        raise ValueError(f"Intake {intake_id} not found")

    intake.status = IntakeStatus.TRIAGING
    db.commit()

    try:
        llm = get_llm_provider()

        # Step 1: Extract PM Brief
        await _extract_pm_brief(db, intake, llm)

        # Step 2: Check for duplicates
        await _check_duplicates(db, intake, llm)

        # Step 3: Generate clarifying questions
        await _generate_questions(db, intake, llm)

        # Update status based on results
        if intake.duplicate_of_id:
            intake.status = IntakeStatus.DUPLICATE
        elif any(q.is_blocking and not q.is_answered for q in intake.clarifying_questions):
            intake.status = IntakeStatus.NEEDS_CLARIFICATION
        else:
            intake.status = IntakeStatus.READY

        db.commit()
        db.refresh(intake)
        return intake

    except Exception as e:
        intake.status = IntakeStatus.NEW
        db.commit()
        raise e


async def _extract_pm_brief(db: Session, intake: Intake, llm) -> None:
    """Extract structured PM brief from intake content."""
    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze this intake and extract a structured PM brief:\n\nTitle: {intake.title}\n\nContent:\n{intake.raw_content}"}
    ]

    _, tool_calls = await llm.complete_with_tools(messages, [INTAKE_TOOLS[0]])

    if tool_calls:
        for call in tool_calls:
            if call["name"] == "extract_pm_brief":
                data = json.loads(call["arguments"])

                # Update intake classification
                intake.inferred_type = IntakeType(data.get("inferred_type", "unknown"))
                intake.type_confidence = data.get("type_confidence", 0.5)
                intake.priority_score = data.get("priority_score")
                intake.priority_rationale = data.get("priority_rationale")

                # Create or update PM Brief
                pm_brief = intake.pm_brief or PMBrief(intake_id=intake.id)
                pm_brief.problem_statement = data.get("problem_statement")
                pm_brief.target_users = json.dumps(data.get("target_users", []))
                pm_brief.use_cases = json.dumps(data.get("use_cases", []))
                pm_brief.north_star_metric = data.get("north_star_metric")
                pm_brief.input_metrics = json.dumps(data.get("input_metrics", []))
                pm_brief.security_constraints = data.get("security_constraints")
                pm_brief.privacy_constraints = data.get("privacy_constraints")
                pm_brief.performance_constraints = data.get("performance_constraints")
                pm_brief.budget_constraints = data.get("budget_constraints")
                pm_brief.compatibility_constraints = data.get("compatibility_constraints")
                pm_brief.assumptions = json.dumps(data.get("assumptions", []))
                pm_brief.out_of_scope = json.dumps(data.get("out_of_scope", []))
                pm_brief.acceptance_criteria = json.dumps(data.get("acceptance_criteria", []))
                pm_brief.team_dependencies = json.dumps(data.get("team_dependencies", []))
                pm_brief.service_dependencies = json.dumps(data.get("service_dependencies", []))
                pm_brief.vendor_dependencies = json.dumps(data.get("vendor_dependencies", []))
                pm_brief.missing_fields = json.dumps(data.get("missing_fields", []))
                pm_brief.extraction_confidence = data.get("extraction_confidence", 0.5)

                if not intake.pm_brief:
                    db.add(pm_brief)

                # Add stakeholders
                for sh_data in data.get("stakeholders", []):
                    stakeholder = IntakeStakeholder(
                        intake_id=intake.id,
                        name=sh_data.get("name", "Unknown"),
                        role=sh_data.get("role", "contributor"),
                        influence=sh_data.get("influence", "medium"),
                        interest=sh_data.get("interest", "medium")
                    )
                    db.add(stakeholder)

                db.commit()


async def _check_duplicates(db: Session, intake: Intake, llm) -> None:
    """Check if intake is a duplicate of existing ones."""
    # Get recent intakes for comparison (excluding current)
    recent_intakes = db.query(Intake).filter(
        Intake.id != intake.id,
        Intake.status.notin_([IntakeStatus.REJECTED, IntakeStatus.DUPLICATE])
    ).order_by(Intake.created_at.desc()).limit(20).all()

    if not recent_intakes:
        return

    existing_summaries = "\n\n".join([
        f"ID {i.id}: {i.title}\nProblem: {i.pm_brief.problem_statement if i.pm_brief else 'N/A'}"
        for i in recent_intakes
    ])

    messages = [
        {"role": "system", "content": DUPLICATE_SYSTEM_PROMPT},
        {"role": "user", "content": f"""Check if this new intake is a duplicate:

NEW INTAKE:
Title: {intake.title}
Problem: {intake.pm_brief.problem_statement if intake.pm_brief else intake.raw_content[:500]}

EXISTING INTAKES:
{existing_summaries}"""}
    ]

    _, tool_calls = await llm.complete_with_tools(messages, [INTAKE_TOOLS[2]])

    if tool_calls:
        for call in tool_calls:
            if call["name"] == "check_duplicate":
                data = json.loads(call["arguments"])
                if data.get("is_duplicate") and data.get("duplicate_of_id"):
                    intake.duplicate_of_id = data["duplicate_of_id"]
                    intake.duplicate_confidence = data.get("confidence", 0.5)
                    db.commit()


async def _generate_questions(db: Session, intake: Intake, llm) -> None:
    """Generate clarifying questions for missing/ambiguous information."""
    if not intake.pm_brief:
        return

    brief = intake.pm_brief
    messages = [
        {"role": "system", "content": CLARIFICATION_SYSTEM_PROMPT},
        {"role": "user", "content": f"""Generate clarifying questions for this intake:

Title: {intake.title}
Problem Statement: {brief.problem_statement or 'Not extracted'}
Missing Fields: {brief.missing_fields or '[]'}
Target Users: {brief.target_users or '[]'}
Acceptance Criteria: {brief.acceptance_criteria or '[]'}
Extraction Confidence: {brief.extraction_confidence}

Raw Content:
{intake.raw_content[:2000]}"""}
    ]

    _, tool_calls = await llm.complete_with_tools(messages, [INTAKE_TOOLS[1]])

    if tool_calls:
        for call in tool_calls:
            if call["name"] == "generate_clarifying_questions":
                data = json.loads(call["arguments"])
                for q_data in data.get("questions", []):
                    question = ClarifyingQuestion(
                        intake_id=intake.id,
                        question=q_data["question"],
                        context=q_data.get("context"),
                        target_field=q_data.get("target_field"),
                        priority=q_data.get("priority", 3),
                        assigned_to=q_data.get("suggested_assignee"),
                        is_blocking=q_data.get("is_blocking", False)
                    )
                    db.add(question)
                db.commit()


async def convert_to_project(db: Session, intake_id: int) -> int:
    """Convert a processed intake into a project with PRD content."""
    from app.models import Project
    from app.models.project import ProjectStatus

    intake = db.query(Intake).filter(Intake.id == intake_id).first()
    if not intake:
        raise ValueError(f"Intake {intake_id} not found")

    if intake.status not in [IntakeStatus.READY, IntakeStatus.NEEDS_CLARIFICATION]:
        raise ValueError(f"Intake must be READY or NEEDS_CLARIFICATION to convert, got {intake.status}")

    # Build PRD content from PM Brief
    prd_content = _build_prd_from_brief(intake)

    project = Project(
        name=intake.title,
        description=intake.pm_brief.problem_statement if intake.pm_brief else None,
        prd_content=prd_content,
        status=ProjectStatus.DRAFT
    )
    db.add(project)
    db.flush()

    intake.status = IntakeStatus.CONVERTED
    intake.converted_to_project_id = project.id
    db.commit()

    return project.id


def _build_prd_from_brief(intake: Intake) -> str:
    """Build PRD markdown from PM Brief."""
    brief = intake.pm_brief
    if not brief:
        return intake.raw_content

    sections = [f"# {intake.title}\n"]

    if brief.problem_statement:
        sections.append(f"## Problem Statement\n{brief.problem_statement}\n")

    target_users = json.loads(brief.target_users) if brief.target_users else []
    if target_users:
        sections.append(f"## Target Users\n" + "\n".join(f"- {u}" for u in target_users) + "\n")

    use_cases = json.loads(brief.use_cases) if brief.use_cases else []
    if use_cases:
        sections.append(f"## Use Cases\n" + "\n".join(f"- {u}" for u in use_cases) + "\n")

    if brief.north_star_metric:
        sections.append(f"## Success Metrics\n**North Star:** {brief.north_star_metric}\n")
        input_metrics = json.loads(brief.input_metrics) if brief.input_metrics else []
        if input_metrics:
            sections.append("**Input Metrics:**\n" + "\n".join(f"- {m}" for m in input_metrics) + "\n")

    # Constraints
    constraints = []
    if brief.security_constraints:
        constraints.append(f"- **Security:** {brief.security_constraints}")
    if brief.privacy_constraints:
        constraints.append(f"- **Privacy:** {brief.privacy_constraints}")
    if brief.performance_constraints:
        constraints.append(f"- **Performance:** {brief.performance_constraints}")
    if brief.budget_constraints:
        constraints.append(f"- **Budget:** {brief.budget_constraints}")
    if brief.compatibility_constraints:
        constraints.append(f"- **Compatibility:** {brief.compatibility_constraints}")
    if constraints:
        sections.append(f"## Constraints\n" + "\n".join(constraints) + "\n")

    assumptions = json.loads(brief.assumptions) if brief.assumptions else []
    if assumptions:
        sections.append(f"## Assumptions\n" + "\n".join(f"- {a}" for a in assumptions) + "\n")

    out_of_scope = json.loads(brief.out_of_scope) if brief.out_of_scope else []
    if out_of_scope:
        sections.append(f"## Out of Scope\n" + "\n".join(f"- {o}" for o in out_of_scope) + "\n")

    criteria = json.loads(brief.acceptance_criteria) if brief.acceptance_criteria else []
    if criteria:
        sections.append(f"## Acceptance Criteria\n" + "\n".join(f"- [ ] {c}" for c in criteria) + "\n")

    # Dependencies
    team_deps = json.loads(brief.team_dependencies) if brief.team_dependencies else []
    service_deps = json.loads(brief.service_dependencies) if brief.service_dependencies else []
    vendor_deps = json.loads(brief.vendor_dependencies) if brief.vendor_dependencies else []
    if team_deps or service_deps or vendor_deps:
        sections.append("## Dependencies\n")
        if team_deps:
            sections.append("**Teams:**\n" + "\n".join(f"- {d}" for d in team_deps) + "\n")
        if service_deps:
            sections.append("**Services:**\n" + "\n".join(f"- {d}" for d in service_deps) + "\n")
        if vendor_deps:
            sections.append("**Vendors:**\n" + "\n".join(f"- {d}" for d in vendor_deps) + "\n")

    return "\n".join(sections)
