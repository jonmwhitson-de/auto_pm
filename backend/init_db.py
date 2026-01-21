"""Initialize the database tables."""
from app.core.database import engine, Base
from app.models import Project, Epic, Story, Task, Sprint, TeamMember

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
