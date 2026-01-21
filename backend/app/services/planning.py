"""Planning services for dependency management, prioritization, and estimation."""
import json
from typing import Any
from sqlalchemy.orm import Session
from app.models import (
    Project, Epic, Story, Task,
    Dependency, DependencyType, DependencyStatus, ItemType,
    Decision, DecisionStatus,
    Assumption, AssumptionStatus, AssumptionRisk,
    StoryEstimate
)
from app.services.llm import get_llm_provider


# RICE Impact scale mapping
RICE_IMPACT_SCALE = {
    "massive": 3.0,
    "high": 2.0,
    "medium": 1.0,
    "low": 0.5,
    "minimal": 0.25
}

# WSJF Fibonacci sequence for relative sizing
WSJF_FIBONACCI = [1, 2, 3, 5, 8, 13, 21]


def calculate_rice_score(reach: int, impact: float, confidence: float, effort: float) -> float:
    """Calculate RICE prioritization score.

    RICE = (Reach * Impact * Confidence) / Effort

    Args:
        reach: Number of users/customers affected per time period
        impact: Impact score (0.25, 0.5, 1, 2, or 3)
        confidence: Confidence percentage (0.5, 0.8, or 1.0)
        effort: Person-months of work
    """
    if effort <= 0:
        return 0
    return (reach * impact * confidence) / effort


def calculate_wsjf_score(
    business_value: int,
    time_criticality: int,
    risk_reduction: int,
    job_size: int
) -> float:
    """Calculate WSJF (Weighted Shortest Job First) score.

    WSJF = Cost of Delay / Job Size
    Cost of Delay = Business Value + Time Criticality + Risk Reduction/Opportunity Enablement

    Args:
        business_value: Relative business value (Fibonacci 1-21)
        time_criticality: Time sensitivity (Fibonacci 1-21)
        risk_reduction: Risk reduction or opportunity enablement value (Fibonacci 1-21)
        job_size: Relative job size (Fibonacci 1-21)
    """
    if job_size <= 0:
        return 0
    cost_of_delay = business_value + time_criticality + risk_reduction
    return cost_of_delay / job_size


def calculate_expected_duration(p10: float, p50: float, p90: float) -> float:
    """Calculate expected duration using PERT-like formula.

    Uses weighted average: (P10 + 4*P50 + P90) / 6
    """
    return (p10 + 4 * p50 + p90) / 6


def get_critical_path(project_id: int, db: Session) -> list[dict]:
    """Calculate critical path through dependencies.

    Returns ordered list of items that form the critical path.
    """
    dependencies = db.query(Dependency).filter(
        Dependency.project_id == project_id,
        Dependency.status != DependencyStatus.RESOLVED
    ).all()

    # Build adjacency list
    graph: dict[str, list[str]] = {}
    durations: dict[str, float] = {}

    for dep in dependencies:
        source_key = f"{dep.source_type.value}:{dep.source_id}"
        target_key = f"{dep.target_type.value}:{dep.target_id}"

        if source_key not in graph:
            graph[source_key] = []
        graph[source_key].append(target_key)

        # Get duration from estimates
        if dep.source_type == ItemType.STORY:
            estimate = db.query(StoryEstimate).filter(
                StoryEstimate.story_id == dep.source_id
            ).first()
            if estimate and estimate.estimate_p50:
                durations[source_key] = estimate.estimate_p50
            else:
                story = db.query(Story).filter(Story.id == dep.source_id).first()
                durations[source_key] = story.estimated_hours or 8 if story else 8
        else:
            durations[source_key] = 8  # Default duration

    # Find all paths and their total durations
    def find_all_paths(start: str, visited: set) -> list[tuple[list[str], float]]:
        if start not in graph or not graph[start]:
            return [([start], durations.get(start, 0))]

        paths = []
        for next_node in graph[start]:
            if next_node not in visited:
                visited.add(next_node)
                sub_paths = find_all_paths(next_node, visited)
                for path, duration in sub_paths:
                    paths.append(([start] + path, durations.get(start, 0) + duration))
                visited.remove(next_node)
        return paths if paths else [([start], durations.get(start, 0))]

    # Find the longest path (critical path)
    all_paths = []
    for node in graph.keys():
        paths = find_all_paths(node, {node})
        all_paths.extend(paths)

    if not all_paths:
        return []

    critical_path, total_duration = max(all_paths, key=lambda x: x[1])

    return [{
        "item": item,
        "duration": durations.get(item, 0),
        "total_duration": total_duration
    } for item in critical_path]


async def infer_dependencies(project_id: int, db: Session) -> list[Dependency]:
    """Use AI to infer dependencies between work items.

    Analyzes stories, epics, and tasks to detect:
    - Technical dependencies (shared code, APIs, data)
    - Logical ordering (must complete X before Y)
    - Cross-team handoffs
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return []

    # Gather all work items
    epics = db.query(Epic).filter(Epic.project_id == project_id).all()
    stories = []
    for epic in epics:
        epic_stories = db.query(Story).filter(Story.epic_id == epic.id).all()
        stories.extend(epic_stories)

    if not stories:
        return []

    # Prepare context for LLM
    items_context = []
    for story in stories:
        items_context.append({
            "type": "story",
            "id": story.id,
            "title": story.title,
            "description": story.description,
            "epic_id": story.epic_id,
            "acceptance_criteria": story.acceptance_criteria
        })

    messages = [
        {
            "role": "system",
            "content": """You are a technical project manager analyzing work items to identify dependencies.

Identify dependencies between items based on:
1. Technical dependencies (shared APIs, databases, services)
2. Logical ordering (feature X requires infrastructure Y)
3. Data flow (output of one feeds into another)
4. Skill/team dependencies (same team, sequential work)

Be conservative - only identify clear, high-confidence dependencies."""
        },
        {
            "role": "user",
            "content": f"""Analyze these work items and identify dependencies between them:

{json.dumps(items_context, indent=2)}

For each dependency, explain:
- Source item (the item that depends on something)
- Target item (the item being depended upon)
- Type: blocks, depends_on, or related
- Confidence score (0-1)
- Reasoning"""
        }
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "record_dependencies",
                "description": "Record inferred dependencies between work items",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dependencies": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source_type": {"type": "string", "enum": ["story", "epic", "task"]},
                                    "source_id": {"type": "integer"},
                                    "target_type": {"type": "string", "enum": ["story", "epic", "task"]},
                                    "target_id": {"type": "integer"},
                                    "dependency_type": {"type": "string", "enum": ["blocks", "depends_on", "related"]},
                                    "confidence": {"type": "number"},
                                    "reasoning": {"type": "string"}
                                },
                                "required": ["source_type", "source_id", "target_type", "target_id", "dependency_type", "confidence", "reasoning"]
                            }
                        }
                    },
                    "required": ["dependencies"]
                }
            }
        }
    ]

    llm = get_llm_provider(db)
    _, tool_calls = await llm.complete_with_tools(messages, tools)

    created_deps = []
    if tool_calls:
        for tc in tool_calls:
            if tc["name"] == "record_dependencies":
                args = json.loads(tc["arguments"])
                for dep_data in args.get("dependencies", []):
                    dep = Dependency(
                        project_id=project_id,
                        source_type=ItemType(dep_data["source_type"]),
                        source_id=dep_data["source_id"],
                        target_type=ItemType(dep_data["target_type"]),
                        target_id=dep_data["target_id"],
                        dependency_type=DependencyType(dep_data["dependency_type"]),
                        inferred=True,
                        confidence=dep_data.get("confidence"),
                        inference_reason=dep_data.get("reasoning")
                    )
                    db.add(dep)
                    created_deps.append(dep)

    db.commit()
    return created_deps


async def generate_range_estimates(story_id: int, db: Session) -> StoryEstimate:
    """Use AI to generate P10/P50/P90 range estimates for a story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise ValueError(f"Story {story_id} not found")

    epic = db.query(Epic).filter(Epic.id == story.epic_id).first()
    tasks = db.query(Task).filter(Task.story_id == story_id).all()

    messages = [
        {
            "role": "system",
            "content": """You are an experienced engineering manager providing effort estimates.

Provide three-point estimates:
- P10 (optimistic): Everything goes perfectly, 10% chance of finishing this fast
- P50 (most likely): Realistic estimate assuming normal conditions
- P90 (pessimistic): Account for unexpected complexity, 90% confident it won't take longer

Consider:
- Technical complexity
- Unknowns and risks
- Dependencies on external factors
- Testing and review time"""
        },
        {
            "role": "user",
            "content": f"""Estimate this story:

Title: {story.title}
Description: {story.description}
Acceptance Criteria: {story.acceptance_criteria}
Epic: {epic.title if epic else 'N/A'}

Tasks:
{json.dumps([{"title": t.title, "description": t.description} for t in tasks], indent=2) if tasks else "No tasks defined"}

Current rough estimate: {story.estimated_hours} hours

Provide P10/P50/P90 estimates in hours."""
        }
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "provide_estimates",
                "description": "Provide three-point range estimates for the story",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "p10_hours": {"type": "number", "description": "Optimistic estimate (10th percentile)"},
                        "p50_hours": {"type": "number", "description": "Most likely estimate (50th percentile)"},
                        "p90_hours": {"type": "number", "description": "Pessimistic estimate (90th percentile)"},
                        "confidence": {"type": "number", "description": "Overall confidence in estimates (0-1)"},
                        "reasoning": {"type": "string", "description": "Explanation of estimation rationale"}
                    },
                    "required": ["p10_hours", "p50_hours", "p90_hours", "confidence", "reasoning"]
                }
            }
        }
    ]

    llm = get_llm_provider(db)
    _, tool_calls = await llm.complete_with_tools(messages, tools)

    # Get or create estimate
    estimate = db.query(StoryEstimate).filter(StoryEstimate.story_id == story_id).first()
    if not estimate:
        estimate = StoryEstimate(story_id=story_id)
        db.add(estimate)

    if tool_calls:
        for tc in tool_calls:
            if tc["name"] == "provide_estimates":
                args = json.loads(tc["arguments"])
                estimate.ai_estimate_p10 = args.get("p10_hours")
                estimate.ai_estimate_p50 = args.get("p50_hours")
                estimate.ai_estimate_p90 = args.get("p90_hours")
                estimate.ai_confidence = args.get("confidence")
                estimate.ai_reasoning = args.get("reasoning")

                # Also set as actual estimates if not already set
                if not estimate.estimate_p10:
                    estimate.estimate_p10 = estimate.ai_estimate_p10
                if not estimate.estimate_p50:
                    estimate.estimate_p50 = estimate.ai_estimate_p50
                if not estimate.estimate_p90:
                    estimate.estimate_p90 = estimate.ai_estimate_p90

    db.commit()
    db.refresh(estimate)
    return estimate


async def extract_decisions_and_assumptions(
    project_id: int,
    content: str,
    source: str,
    db: Session
) -> tuple[list[Decision], list[Assumption]]:
    """Extract decisions and assumptions from text content (PRD, meeting notes, etc.)."""

    messages = [
        {
            "role": "system",
            "content": """You are a technical analyst extracting key decisions and assumptions from project documentation.

Decisions are choices that have been made (or need to be made) about:
- Technology choices
- Architecture patterns
- Scope boundaries
- Trade-offs

Assumptions are beliefs or conditions that are assumed to be true but need validation:
- Technical feasibility
- Resource availability
- External dependencies
- User behavior"""
        },
        {
            "role": "user",
            "content": f"""Extract decisions and assumptions from this content:

{content}

For each decision, capture the context, the actual decision, rationale, and alternatives considered.
For each assumption, capture the assumption, its impact if wrong, and suggested validation approach."""
        }
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "record_decisions_and_assumptions",
                "description": "Record extracted decisions and assumptions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "decisions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "context": {"type": "string"},
                                    "decision": {"type": "string"},
                                    "rationale": {"type": "string"},
                                    "alternatives": {"type": "array", "items": {"type": "string"}},
                                    "status": {"type": "string", "enum": ["proposed", "accepted"]}
                                },
                                "required": ["title", "decision"]
                            }
                        },
                        "assumptions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "assumption": {"type": "string"},
                                    "context": {"type": "string"},
                                    "impact_if_wrong": {"type": "string"},
                                    "validation_method": {"type": "string"},
                                    "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
                                },
                                "required": ["assumption"]
                            }
                        }
                    },
                    "required": ["decisions", "assumptions"]
                }
            }
        }
    ]

    llm = get_llm_provider(db)
    _, tool_calls = await llm.complete_with_tools(messages, tools)

    created_decisions = []
    created_assumptions = []

    if tool_calls:
        for tc in tool_calls:
            if tc["name"] == "record_decisions_and_assumptions":
                args = json.loads(tc["arguments"])

                for dec_data in args.get("decisions", []):
                    decision = Decision(
                        project_id=project_id,
                        title=dec_data["title"],
                        context=dec_data.get("context"),
                        decision=dec_data["decision"],
                        rationale=dec_data.get("rationale"),
                        alternatives=json.dumps(dec_data.get("alternatives", [])),
                        status=DecisionStatus(dec_data.get("status", "proposed")),
                        extracted_from=source,
                        extraction_confidence=0.8
                    )
                    db.add(decision)
                    created_decisions.append(decision)

                for asm_data in args.get("assumptions", []):
                    assumption = Assumption(
                        project_id=project_id,
                        assumption=asm_data["assumption"],
                        context=asm_data.get("context"),
                        impact_if_wrong=asm_data.get("impact_if_wrong"),
                        validation_method=asm_data.get("validation_method"),
                        risk_level=AssumptionRisk(asm_data.get("risk_level", "medium")),
                        extracted_from=source,
                        extraction_confidence=0.8
                    )
                    db.add(assumption)
                    created_assumptions.append(assumption)

    db.commit()
    return created_decisions, created_assumptions


def update_story_prioritization(
    story_id: int,
    model: str,
    scores: dict,
    db: Session
) -> StoryEstimate:
    """Update prioritization scores for a story.

    Args:
        story_id: ID of the story
        model: Prioritization model ('rice', 'wsjf', 'cod')
        scores: Dict of score components
        db: Database session
    """
    estimate = db.query(StoryEstimate).filter(StoryEstimate.story_id == story_id).first()
    if not estimate:
        estimate = StoryEstimate(story_id=story_id)
        db.add(estimate)

    if model == "rice":
        estimate.rice_reach = scores.get("reach")
        estimate.rice_impact = scores.get("impact")
        estimate.rice_confidence = scores.get("confidence")
        estimate.rice_effort = scores.get("effort")
        if all([estimate.rice_reach, estimate.rice_impact, estimate.rice_confidence, estimate.rice_effort]):
            estimate.rice_score = calculate_rice_score(
                estimate.rice_reach,
                estimate.rice_impact,
                estimate.rice_confidence,
                estimate.rice_effort
            )

    elif model == "wsjf":
        estimate.wsjf_business_value = scores.get("business_value")
        estimate.wsjf_time_criticality = scores.get("time_criticality")
        estimate.wsjf_risk_reduction = scores.get("risk_reduction")
        estimate.wsjf_job_size = scores.get("job_size")
        if all([estimate.wsjf_business_value, estimate.wsjf_time_criticality,
                estimate.wsjf_risk_reduction, estimate.wsjf_job_size]):
            estimate.wsjf_score = calculate_wsjf_score(
                estimate.wsjf_business_value,
                estimate.wsjf_time_criticality,
                estimate.wsjf_risk_reduction,
                estimate.wsjf_job_size
            )

    elif model == "cod":
        estimate.cod_weekly = scores.get("weekly_cost")
        estimate.cod_urgency_profile = scores.get("urgency_profile")

    db.commit()
    db.refresh(estimate)
    return estimate
