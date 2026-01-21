from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import create_tables
from app.api import projects, epics, stories, tasks, sprints, team_members, analyze, admin, intake, planning, lifecycle
# Import all models to ensure they're registered with Base
from app.models import *  # noqa: F401, F403

app = FastAPI(
    title=settings.app_name,
    description="AI-powered automated project management",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5209"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(epics.router, prefix="/api/epics", tags=["epics"])
app.include_router(stories.router, prefix="/api/stories", tags=["stories"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(sprints.router, prefix="/api/sprints", tags=["sprints"])
app.include_router(team_members.router, prefix="/api/team-members", tags=["team-members"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(intake.router, prefix="/api/intake", tags=["intake"])
app.include_router(planning.router, prefix="/api/planning", tags=["planning"])
app.include_router(lifecycle.router, prefix="/api/lifecycle", tags=["lifecycle"])


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    create_tables()


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "llm_provider": settings.llm_provider}
