# Auto PM - AI-Powered Project Manager

An automated project management tool that leverages AI to analyze PRDs and generate work breakdowns, backlog items, and sprint plans.

## Features

- **PRD Analysis**: Upload a Word document or paste PRD text, and the AI generates:
  - Epics (major feature areas)
  - User Stories with acceptance criteria
  - Tasks for each story
  - Story point and hour estimates

- **Sprint Planning**: Create sprints, assign stories, and track capacity

- **Team Management**: Define team members and their sprint capacity

## Tech Stack

- **Backend**: Python, FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: React, TypeScript, Vite, TailwindCSS
- **AI**: MCP-compatible tool calling, Azure OpenAI (or stub for development)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 1. Start the Database

```bash
docker-compose up -d
```

### 2. Set Up Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### 3. Set Up Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Access the App

Open http://localhost:5173 in your browser.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/autopm` |
| `LLM_PROVIDER` | `stub` or `azure_openai` | `stub` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | - |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | - |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name | `gpt-4` |

### Using Azure OpenAI

1. Set `LLM_PROVIDER=azure_openai` in `.env`
2. Configure your Azure OpenAI credentials
3. Restart the backend

## API Endpoints

- `POST /api/projects` - Create project with PRD text
- `POST /api/projects/upload` - Create project from Word doc
- `POST /api/analyze` - Analyze PRD and generate work breakdown
- `GET /api/projects/{id}` - Get project with full breakdown
- `POST /api/sprints` - Create sprint
- `POST /api/sprints/plan` - Assign stories to sprint
- `GET /api/sprints/project/{id}` - List sprints for project
- `POST /api/team-members` - Add team member
- `GET /api/team-members/project/{id}/capacity` - Get team capacity
