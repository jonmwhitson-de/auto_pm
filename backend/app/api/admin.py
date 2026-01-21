from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import os

from app.core.database import get_db
from app.core.config import settings
from app.models import SystemSettings, MCPTool, Integration

router = APIRouter()


# ============ LLM Configuration ============

class LLMConfigResponse(BaseModel):
    provider: str
    azure_endpoint: Optional[str]
    azure_deployment: str
    azure_api_version: str
    has_api_key: bool


class LLMConfigUpdate(BaseModel):
    provider: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_deployment: Optional[str] = None
    azure_api_key: Optional[str] = None


@router.get("/llm-config", response_model=LLMConfigResponse)
def get_llm_config(db: Session = Depends(get_db)):
    """Get current LLM configuration."""
    # Check for overrides in database
    provider_setting = db.query(SystemSettings).filter(SystemSettings.key == "llm_provider").first()
    endpoint_setting = db.query(SystemSettings).filter(SystemSettings.key == "azure_openai_endpoint").first()
    deployment_setting = db.query(SystemSettings).filter(SystemSettings.key == "azure_openai_deployment").first()

    return LLMConfigResponse(
        provider=provider_setting.value if provider_setting else settings.llm_provider,
        azure_endpoint=endpoint_setting.value if endpoint_setting else settings.azure_openai_endpoint,
        azure_deployment=deployment_setting.value if deployment_setting else settings.azure_openai_deployment,
        azure_api_version=settings.azure_openai_api_version,
        has_api_key=bool(settings.azure_openai_api_key or db.query(SystemSettings).filter(SystemSettings.key == "azure_openai_api_key").first()),
    )


@router.patch("/llm-config", response_model=LLMConfigResponse)
def update_llm_config(update: LLMConfigUpdate, db: Session = Depends(get_db)):
    """Update LLM configuration."""
    def set_setting(key: str, value: str):
        setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
        if setting:
            setting.value = value
        else:
            db.add(SystemSettings(key=key, value=value))

    if update.provider is not None:
        if update.provider not in ["stub", "azure_openai"]:
            raise HTTPException(status_code=400, detail="Invalid provider. Must be 'stub' or 'azure_openai'")
        set_setting("llm_provider", update.provider)

    if update.azure_endpoint is not None:
        set_setting("azure_openai_endpoint", update.azure_endpoint)

    if update.azure_deployment is not None:
        set_setting("azure_openai_deployment", update.azure_deployment)

    if update.azure_api_key is not None:
        set_setting("azure_openai_api_key", update.azure_api_key)

    db.commit()
    return get_llm_config(db)


# ============ MCP Tools ============

class MCPToolResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    enabled: bool
    config: Optional[dict]

    class Config:
        from_attributes = True


class MCPToolUpdate(BaseModel):
    enabled: Optional[bool] = None
    config: Optional[dict] = None


# Default tools to seed
DEFAULT_TOOLS = [
    {
        "name": "create_work_breakdown",
        "description": "Analyzes PRD and generates epics, stories, and tasks with estimates",
    },
    {
        "name": "estimate_story",
        "description": "Provides story point and hour estimates for a user story",
    },
    {
        "name": "suggest_sprint_plan",
        "description": "Suggests optimal story assignments for a sprint based on capacity",
    },
    {
        "name": "generate_acceptance_criteria",
        "description": "Generates acceptance criteria for a user story",
    },
    {
        "name": "identify_dependencies",
        "description": "Identifies dependencies between stories and suggests ordering",
    },
    {
        "name": "risk_assessment",
        "description": "Analyzes stories for technical risks and suggests mitigation",
    },
]


@router.get("/tools", response_model=list[MCPToolResponse])
def list_tools(db: Session = Depends(get_db)):
    """List all MCP tools."""
    tools = db.query(MCPTool).all()

    # Seed default tools if none exist
    if not tools:
        for tool_data in DEFAULT_TOOLS:
            tool = MCPTool(
                name=tool_data["name"],
                description=tool_data["description"],
                enabled=True,
            )
            db.add(tool)
        db.commit()
        tools = db.query(MCPTool).all()

    return [
        MCPToolResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            enabled=t.enabled,
            config=json.loads(t.config) if t.config else None,
        )
        for t in tools
    ]


@router.patch("/tools/{tool_id}", response_model=MCPToolResponse)
def update_tool(tool_id: int, update: MCPToolUpdate, db: Session = Depends(get_db)):
    """Update a tool's configuration."""
    tool = db.query(MCPTool).filter(MCPTool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    if update.enabled is not None:
        tool.enabled = update.enabled
    if update.config is not None:
        tool.config = json.dumps(update.config)

    db.commit()
    db.refresh(tool)

    return MCPToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        enabled=tool.enabled,
        config=json.loads(tool.config) if tool.config else None,
    )


# ============ Integrations ============

class IntegrationResponse(BaseModel):
    id: int
    name: str
    display_name: str
    enabled: bool
    status: str
    last_sync: Optional[str]
    config_keys: list[str]  # List of configured keys (not values for security)

    class Config:
        from_attributes = True


class IntegrationUpdate(BaseModel):
    enabled: Optional[bool] = None
    config: Optional[dict] = None


# Default integrations to seed
DEFAULT_INTEGRATIONS = [
    {"name": "outlook", "display_name": "Microsoft Outlook Calendar"},
    {"name": "google_calendar", "display_name": "Google Calendar"},
    {"name": "teams", "display_name": "Microsoft Teams"},
    {"name": "slack", "display_name": "Slack"},
]


@router.get("/integrations", response_model=list[IntegrationResponse])
def list_integrations(db: Session = Depends(get_db)):
    """List all integrations."""
    integrations = db.query(Integration).all()

    # Seed default integrations if none exist
    if not integrations:
        for int_data in DEFAULT_INTEGRATIONS:
            integration = Integration(
                name=int_data["name"],
                display_name=int_data["display_name"],
                enabled=False,
                status="disconnected",
            )
            db.add(integration)
        db.commit()
        integrations = db.query(Integration).all()

    return [
        IntegrationResponse(
            id=i.id,
            name=i.name,
            display_name=i.display_name,
            enabled=i.enabled,
            status=i.status,
            last_sync=i.last_sync.isoformat() if i.last_sync else None,
            config_keys=list(json.loads(i.config).keys()) if i.config else [],
        )
        for i in integrations
    ]


@router.patch("/integrations/{integration_id}", response_model=IntegrationResponse)
def update_integration(integration_id: int, update: IntegrationUpdate, db: Session = Depends(get_db)):
    """Update an integration's configuration."""
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    if update.enabled is not None:
        integration.enabled = update.enabled
        if not update.enabled:
            integration.status = "disconnected"

    if update.config is not None:
        # Merge with existing config
        existing_config = json.loads(integration.config) if integration.config else {}
        existing_config.update(update.config)
        integration.config = json.dumps(existing_config)

    db.commit()
    db.refresh(integration)

    return IntegrationResponse(
        id=integration.id,
        name=integration.name,
        display_name=integration.display_name,
        enabled=integration.enabled,
        status=integration.status,
        last_sync=integration.last_sync.isoformat() if integration.last_sync else None,
        config_keys=list(json.loads(integration.config).keys()) if integration.config else [],
    )


@router.post("/integrations/{integration_id}/test")
def test_integration(integration_id: int, db: Session = Depends(get_db)):
    """Test an integration connection."""
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    # TODO: Implement actual connection testing for each integration type
    # For now, return a mock response
    return {
        "success": False,
        "message": f"Integration testing for {integration.display_name} not yet implemented. Configure credentials and enable when ready.",
    }
