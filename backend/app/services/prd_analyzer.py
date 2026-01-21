from sqlalchemy.orm import Session
from app.services.llm import get_llm_provider
from app.models import Project, Epic, Story, Task
from app.models.project import ProjectStatus
from app.models.epic import Priority
from app.models.story import StoryStatus
from app.models.task import TaskStatus
import json

# MCP Tool definitions for work breakdown
WORK_BREAKDOWN_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_work_breakdown",
            "description": "Create a complete work breakdown structure from a PRD, including epics, stories, and tasks with estimates",
            "parameters": {
                "type": "object",
                "properties": {
                    "epics": {
                        "type": "array",
                        "description": "List of epics derived from the PRD",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "Epic title"},
                                "description": {"type": "string", "description": "Epic description"},
                                "priority": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high", "critical"],
                                },
                                "stories": {
                                    "type": "array",
                                    "description": "User stories within this epic",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "description": {
                                                "type": "string",
                                                "description": "User story in 'As a... I want... So that...' format",
                                            },
                                            "acceptance_criteria": {
                                                "type": "string",
                                                "description": "Acceptance criteria as bullet points",
                                            },
                                            "story_points": {
                                                "type": "integer",
                                                "description": "Fibonacci story points (1, 2, 3, 5, 8, 13)",
                                            },
                                            "estimated_hours": {
                                                "type": "integer",
                                                "description": "Estimated hours to complete",
                                            },
                                            "priority": {
                                                "type": "string",
                                                "enum": ["low", "medium", "high", "critical"],
                                            },
                                            "tasks": {
                                                "type": "array",
                                                "description": "Technical tasks to implement this story",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "title": {"type": "string"},
                                                        "description": {"type": "string"},
                                                        "estimated_hours": {"type": "integer"},
                                                    },
                                                    "required": ["title"],
                                                },
                                            },
                                        },
                                        "required": ["title", "description"],
                                    },
                                },
                            },
                            "required": ["title", "description", "stories"],
                        },
                    }
                },
                "required": ["epics"],
            },
        },
    }
]

SYSTEM_PROMPT = """You are an expert project manager and software architect. Your task is to analyze a Product Requirements Document (PRD) and create a complete work breakdown structure.

For the given PRD, you must:
1. Identify logical epics (major feature areas or themes)
2. Break each epic into user stories following the format "As a [user], I want [feature] so that [benefit]"
3. Define clear acceptance criteria for each story
4. Estimate story points using Fibonacci scale (1, 2, 3, 5, 8, 13)
5. Estimate hours for each story
6. Break stories into technical implementation tasks
7. Assign priorities based on business value and dependencies

Consider:
- Dependencies between stories
- Technical complexity
- Risk areas that need spike/research
- MVP vs future enhancements
- Cross-cutting concerns (security, performance, testing)

Use the create_work_breakdown tool to structure your analysis."""


async def analyze_prd(db: Session, project_id: int) -> Project:
    """Analyze a project's PRD and generate work breakdown."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    project.status = ProjectStatus.ANALYZING
    db.commit()

    try:
        llm = get_llm_provider()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Please analyze this PRD and create a work breakdown:\n\n{project.prd_content}",
            },
        ]

        _, tool_calls = await llm.complete_with_tools(messages, WORK_BREAKDOWN_TOOLS)

        if tool_calls:
            for tool_call in tool_calls:
                if tool_call["name"] == "create_work_breakdown":
                    breakdown = json.loads(tool_call["arguments"])
                    _create_work_items(db, project, breakdown)

        project.status = ProjectStatus.READY
        db.commit()
        db.refresh(project)
        return project

    except Exception as e:
        project.status = ProjectStatus.DRAFT
        db.commit()
        raise e


def _create_work_items(db: Session, project: Project, breakdown: dict) -> None:
    """Create database records from work breakdown."""
    priority_map = {
        "low": Priority.LOW,
        "medium": Priority.MEDIUM,
        "high": Priority.HIGH,
        "critical": Priority.CRITICAL,
    }

    for epic_order, epic_data in enumerate(breakdown.get("epics", [])):
        epic = Epic(
            project_id=project.id,
            title=epic_data["title"],
            description=epic_data.get("description", ""),
            priority=priority_map.get(epic_data.get("priority", "medium"), Priority.MEDIUM),
            order=epic_order,
        )
        db.add(epic)
        db.flush()

        for story_order, story_data in enumerate(epic_data.get("stories", [])):
            story = Story(
                epic_id=epic.id,
                title=story_data["title"],
                description=story_data.get("description", ""),
                acceptance_criteria=story_data.get("acceptance_criteria", ""),
                story_points=story_data.get("story_points"),
                estimated_hours=story_data.get("estimated_hours"),
                priority=priority_map.get(story_data.get("priority", "medium"), Priority.MEDIUM),
                status=StoryStatus.BACKLOG,
                order=story_order,
            )
            db.add(story)
            db.flush()

            for task_order, task_data in enumerate(story_data.get("tasks", [])):
                task = Task(
                    story_id=story.id,
                    title=task_data["title"],
                    description=task_data.get("description", ""),
                    estimated_hours=task_data.get("estimated_hours"),
                    status=TaskStatus.TODO,
                    order=task_order,
                )
                db.add(task)

    db.commit()
