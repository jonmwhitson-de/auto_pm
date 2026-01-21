from abc import ABC, abstractmethod
from typing import Any, Optional
import json
from sqlalchemy.orm import Session
from app.core.config import settings


def get_db_setting(db: Optional[Session], key: str, default: Any = None) -> Any:
    """Get a setting from the database, falling back to environment config."""
    if db is None:
        return default

    from app.models import SystemSettings
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if setting and setting.value:
        return setting.value
    return default


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Send a completion request to the LLM."""
        pass

    @abstractmethod
    async def complete_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> tuple[str | None, list[dict] | None]:
        """Send a completion request and handle tool calls."""
        pass


class StubLLMProvider(LLMProvider):
    """Stub LLM for development and testing."""

    async def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        return {
            "content": "[STUB] This is a stub response. Configure Azure OpenAI for real responses.",
            "tool_calls": None,
        }

    async def complete_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> tuple[str | None, list[dict] | None]:
        # Determine which tool is being requested
        tool_names = [t["function"]["name"] for t in tools if "function" in t]

        # Handle intake processing tools
        if "extract_pm_brief" in tool_names:
            sample_brief = {
                "inferred_type": "feature",
                "type_confidence": 0.85,
                "priority_score": 75,
                "priority_rationale": "High business impact - blocking deals, clear requirements, reasonable scope",
                "problem_statement": "Enterprise customers need the ability to export analytics reports to PDF format for offline viewing and sharing.",
                "target_users": ["Enterprise customers", "Sales teams", "Executives"],
                "use_cases": [
                    "Export individual reports for offline review",
                    "Share reports with stakeholders without system access",
                    "Include in presentations and proposals"
                ],
                "north_star_metric": "Report export adoption rate",
                "input_metrics": ["Number of exports per week", "Export completion rate", "Time to generate PDF"],
                "security_constraints": "Reports may contain sensitive business data - ensure secure generation",
                "privacy_constraints": "Must respect data access permissions in exports",
                "performance_constraints": "Support reports up to 100 pages within reasonable time (<30s)",
                "budget_constraints": None,
                "compatibility_constraints": "PDF format must be compatible with standard viewers",
                "assumptions": [
                    "Users have permission to view the data they export",
                    "Existing report rendering can be adapted for PDF",
                    "Company branding assets are available"
                ],
                "out_of_scope": [
                    "Bulk/scheduled exports",
                    "Export to formats other than PDF",
                    "Email delivery of exports"
                ],
                "acceptance_criteria": [
                    "User can export any single report to PDF",
                    "User can select custom date range before export",
                    "Exported PDF includes company logo in header",
                    "Export completes within 30 seconds for 100-page reports"
                ],
                "team_dependencies": ["Platform team for PDF generation service"],
                "service_dependencies": ["Report rendering service", "Asset storage"],
                "vendor_dependencies": [],
                "stakeholders": [
                    {"name": "Sarah Johnson", "role": "decision_maker", "influence": "high", "interest": "high"},
                    {"name": "Engineering Lead", "role": "contributor", "influence": "medium", "interest": "high"}
                ],
                "missing_fields": ["budget_constraints", "specific_deadline"],
                "extraction_confidence": 0.78
            }
            return None, [{"name": "extract_pm_brief", "arguments": json.dumps(sample_brief)}]

        if "generate_clarifying_questions" in tool_names:
            sample_questions = {
                "questions": [
                    {
                        "question": "What is the target deadline for this feature?",
                        "context": "Understanding timeline helps prioritize and plan resources",
                        "target_field": "deadline",
                        "priority": 1,
                        "suggested_assignee": "Product Manager",
                        "is_blocking": True
                    },
                    {
                        "question": "Should the PDF export preserve interactive elements (links, bookmarks)?",
                        "context": "Affects technical complexity and user experience",
                        "target_field": "acceptance_criteria",
                        "priority": 2,
                        "suggested_assignee": "Sarah Johnson",
                        "is_blocking": False
                    },
                    {
                        "question": "Is there a budget allocated for third-party PDF generation services?",
                        "context": "Build vs buy decision for PDF generation",
                        "target_field": "budget_constraints",
                        "priority": 3,
                        "suggested_assignee": "Engineering Lead",
                        "is_blocking": False
                    }
                ]
            }
            return None, [{"name": "generate_clarifying_questions", "arguments": json.dumps(sample_questions)}]

        if "check_duplicate" in tool_names:
            sample_duplicate = {
                "is_duplicate": False,
                "confidence": 0.1,
                "evidence": "No similar requests found in recent intakes"
            }
            return None, [{"name": "check_duplicate", "arguments": json.dumps(sample_duplicate)}]

        # Handle planning tools
        if "record_dependencies" in tool_names:
            sample_dependencies = {
                "dependencies": [
                    {
                        "source_type": "story",
                        "source_id": 2,
                        "target_type": "story",
                        "target_id": 1,
                        "dependency_type": "depends_on",
                        "confidence": 0.85,
                        "reasoning": "Story 2 requires the API endpoints from Story 1 to be completed first"
                    }
                ]
            }
            return None, [{"name": "record_dependencies", "arguments": json.dumps(sample_dependencies)}]

        if "provide_estimates" in tool_names:
            sample_estimates = {
                "p10_hours": 4,
                "p50_hours": 8,
                "p90_hours": 16,
                "confidence": 0.7,
                "reasoning": "Based on typical feature complexity. P10 assumes familiar tech stack and no blockers. P50 accounts for standard integration work. P90 includes buffer for unexpected complexity or dependency delays."
            }
            return None, [{"name": "provide_estimates", "arguments": json.dumps(sample_estimates)}]

        if "record_decisions_and_assumptions" in tool_names:
            sample_extraction = {
                "decisions": [
                    {
                        "title": "Use PostgreSQL for primary database",
                        "context": "Need to choose a database for storing project data",
                        "decision": "Use PostgreSQL as the primary database",
                        "rationale": "PostgreSQL provides robust ACID compliance, JSON support, and scales well",
                        "alternatives": ["MySQL", "MongoDB", "SQLite"],
                        "status": "accepted"
                    }
                ],
                "assumptions": [
                    {
                        "assumption": "Team has experience with React",
                        "context": "Frontend technology choice",
                        "impact_if_wrong": "Would need additional training time, potentially 2-4 weeks",
                        "validation_method": "Survey team members about React experience",
                        "risk_level": "medium"
                    },
                    {
                        "assumption": "API response times will be under 200ms",
                        "context": "Performance requirements",
                        "impact_if_wrong": "May need to add caching layer or optimize queries",
                        "validation_method": "Load testing during development",
                        "risk_level": "high"
                    }
                ]
            }
            return None, [{"name": "record_decisions_and_assumptions", "arguments": json.dumps(sample_extraction)}]

        # Handle lifecycle analysis tool
        if "generate_offer_lifecycle_tasks" in tool_names:
            sample_lifecycle = {
                "phases": [
                    {
                        "phase": "concept",
                        "target_duration_days": 21,
                        "tasks": [
                            {"title": "Market Opportunity Analysis", "definition": "Conduct comprehensive market analysis to validate opportunity size and competitive landscape", "category": "Product Management", "days_required": 5, "owner_team": "Product", "is_required": True, "confidence": 0.9, "reasoning": "Essential for business case validation"},
                            {"title": "Competitive Landscape Review", "definition": "Analyze competing solutions and identify differentiation opportunities", "category": "Product Management", "days_required": 4, "owner_team": "Product", "is_required": True, "confidence": 0.9, "reasoning": "Critical for positioning"},
                            {"title": "Business Case Development", "definition": "Create business case including ROI, investment requirements, and revenue projections", "category": "Finance & Pricing", "days_required": 7, "owner_team": "Finance", "is_required": True, "confidence": 0.95, "reasoning": "Required for executive approval"},
                            {"title": "Executive Sponsorship Alignment", "definition": "Secure executive sponsor and align on strategic objectives", "category": "Product Management", "days_required": 3, "owner_team": "Leadership", "is_required": True, "confidence": 0.9, "reasoning": "Governance requirement"},
                            {"title": "Initial Legal Review", "definition": "Preliminary review of regulatory and compliance requirements", "category": "Legal & Compliance", "days_required": 5, "owner_team": "Legal", "is_required": True, "confidence": 0.85, "reasoning": "Early risk identification"},
                            {"title": "Customer Discovery Interviews", "definition": "Conduct interviews with target customers to validate problem and solution fit", "category": "Product Management", "days_required": 7, "owner_team": "Product", "is_required": True, "confidence": 0.9, "reasoning": "Voice of customer input"},
                            {"title": "Technical Feasibility Assessment", "definition": "Assess technical feasibility and identify major technical risks", "category": "Engineering & Technical", "days_required": 5, "owner_team": "Engineering", "is_required": True, "confidence": 0.85, "reasoning": "Validate buildability"},
                            {"title": "Partner Ecosystem Analysis", "definition": "Identify potential partner opportunities and requirements", "category": "Partner & Ecosystem", "days_required": 4, "owner_team": "Partnerships", "is_required": False, "confidence": 0.7, "reasoning": "Partner leverage opportunities"},
                            {"title": "Initial Pricing Hypothesis", "definition": "Develop initial pricing model hypothesis based on value analysis", "category": "Finance & Pricing", "days_required": 3, "owner_team": "Finance", "is_required": True, "confidence": 0.8, "reasoning": "Business model validation"},
                            {"title": "Resource Requirements Estimate", "definition": "High-level estimate of resources needed across all phases", "category": "Operations & Support", "days_required": 3, "owner_team": "PMO", "is_required": True, "confidence": 0.75, "reasoning": "Planning input"},
                            {"title": "Risk Assessment Workshop", "definition": "Conduct risk identification and assessment workshop with stakeholders", "category": "Quality & Certification", "days_required": 2, "owner_team": "Risk", "is_required": True, "confidence": 0.85, "reasoning": "Risk management"},
                            {"title": "Concept Phase Gate Preparation", "definition": "Prepare materials for concept phase exit review", "category": "Product Management", "days_required": 2, "owner_team": "Product", "is_required": True, "confidence": 0.95, "reasoning": "Phase exit requirement"}
                        ]
                    },
                    {
                        "phase": "define",
                        "target_duration_days": 28,
                        "tasks": [
                            {"title": "Solution Architecture Design", "definition": "Define technical architecture and integration requirements", "category": "Engineering & Technical", "days_required": 10, "owner_team": "Architecture", "is_required": True, "confidence": 0.9, "reasoning": "Foundation for development"},
                            {"title": "Detailed Requirements Documentation", "definition": "Document functional and non-functional requirements", "category": "Product Management", "days_required": 8, "owner_team": "Product", "is_required": True, "confidence": 0.95, "reasoning": "Development input"},
                            {"title": "Service Level Definitions", "definition": "Define SLAs, support tiers, and escalation procedures", "category": "Operations & Support", "days_required": 5, "owner_team": "Operations", "is_required": True, "confidence": 0.9, "reasoning": "Operational readiness"},
                            {"title": "Pricing Model Finalization", "definition": "Finalize pricing structure, tiers, and terms", "category": "Finance & Pricing", "days_required": 7, "owner_team": "Finance", "is_required": True, "confidence": 0.9, "reasoning": "Revenue model"},
                            {"title": "Contract Template Development", "definition": "Develop standard contract templates and terms", "category": "Legal & Compliance", "days_required": 10, "owner_team": "Legal", "is_required": True, "confidence": 0.9, "reasoning": "Sales enablement"},
                            {"title": "Security Requirements Definition", "definition": "Define security requirements and compliance certifications needed", "category": "Engineering & Technical", "days_required": 5, "owner_team": "Security", "is_required": True, "confidence": 0.9, "reasoning": "Security compliance"},
                            {"title": "Data Privacy Impact Assessment", "definition": "Conduct DPIA and define data handling procedures", "category": "Legal & Compliance", "days_required": 7, "owner_team": "Privacy", "is_required": True, "confidence": 0.85, "reasoning": "Privacy compliance"},
                            {"title": "Service Delivery Model Design", "definition": "Design service delivery model including resource types and ratios", "category": "Operations & Support", "days_required": 6, "owner_team": "Services", "is_required": True, "confidence": 0.9, "reasoning": "Delivery planning"},
                            {"title": "Partner Requirements Definition", "definition": "Define partner certifications, training, and enablement requirements", "category": "Partner & Ecosystem", "days_required": 5, "owner_team": "Partnerships", "is_required": False, "confidence": 0.75, "reasoning": "Partner channel"},
                            {"title": "Integration Requirements", "definition": "Document integration requirements with existing systems", "category": "Engineering & Technical", "days_required": 5, "owner_team": "Integration", "is_required": True, "confidence": 0.85, "reasoning": "Technical integration"},
                            {"title": "Customer Success Model", "definition": "Define customer success engagement model and metrics", "category": "Operations & Support", "days_required": 4, "owner_team": "Customer Success", "is_required": True, "confidence": 0.85, "reasoning": "Customer retention"},
                            {"title": "Billing System Requirements", "definition": "Define billing system integration and invoicing requirements", "category": "Finance & Pricing", "days_required": 4, "owner_team": "Finance", "is_required": True, "confidence": 0.8, "reasoning": "Revenue operations"},
                            {"title": "Support Process Design", "definition": "Design support processes, tools, and escalation paths", "category": "Operations & Support", "days_required": 5, "owner_team": "Support", "is_required": True, "confidence": 0.9, "reasoning": "Support readiness"},
                            {"title": "Competitive Positioning", "definition": "Finalize competitive positioning and differentiation messaging", "category": "Marketing & Communications", "days_required": 4, "owner_team": "Marketing", "is_required": True, "confidence": 0.85, "reasoning": "Go-to-market"},
                            {"title": "Define Phase Gate Preparation", "definition": "Prepare materials for define phase exit review", "category": "Product Management", "days_required": 2, "owner_team": "Product", "is_required": True, "confidence": 0.95, "reasoning": "Phase exit requirement"}
                        ]
                    },
                    {
                        "phase": "plan",
                        "target_duration_days": 28,
                        "tasks": [
                            {"title": "Go-to-Market Strategy", "definition": "Develop comprehensive GTM strategy including channels and timing", "category": "Marketing & Communications", "days_required": 10, "owner_team": "Marketing", "is_required": True, "confidence": 0.9, "reasoning": "Launch success"},
                            {"title": "Sales Enablement Plan", "definition": "Create sales training and enablement plan", "category": "Sales Enablement", "days_required": 7, "owner_team": "Sales Ops", "is_required": True, "confidence": 0.9, "reasoning": "Sales readiness"},
                            {"title": "Resource Staffing Plan", "definition": "Develop detailed staffing plan with hiring timeline", "category": "Operations & Support", "days_required": 6, "owner_team": "HR", "is_required": True, "confidence": 0.85, "reasoning": "Delivery capacity"},
                            {"title": "Development Sprint Planning", "definition": "Plan development sprints and milestones", "category": "Engineering & Technical", "days_required": 5, "owner_team": "Engineering", "is_required": True, "confidence": 0.9, "reasoning": "Development timeline"},
                            {"title": "Partner Enablement Plan", "definition": "Create partner onboarding and certification plan", "category": "Partner & Ecosystem", "days_required": 5, "owner_team": "Partnerships", "is_required": False, "confidence": 0.75, "reasoning": "Partner channel"},
                            {"title": "Training Curriculum Development Plan", "definition": "Plan training content development for all audiences", "category": "Training & Documentation", "days_required": 5, "owner_team": "Training", "is_required": True, "confidence": 0.85, "reasoning": "Enablement"},
                            {"title": "Marketing Campaign Plan", "definition": "Develop marketing campaign calendar and content plan", "category": "Marketing & Communications", "days_required": 6, "owner_team": "Marketing", "is_required": True, "confidence": 0.85, "reasoning": "Demand generation"},
                            {"title": "Launch Timeline Development", "definition": "Create detailed launch timeline with dependencies", "category": "Product Management", "days_required": 4, "owner_team": "Product", "is_required": True, "confidence": 0.9, "reasoning": "Launch coordination"},
                            {"title": "Budget Finalization", "definition": "Finalize budget allocation across all workstreams", "category": "Finance & Pricing", "days_required": 5, "owner_team": "Finance", "is_required": True, "confidence": 0.9, "reasoning": "Financial planning"},
                            {"title": "Risk Mitigation Planning", "definition": "Develop risk mitigation strategies and contingency plans", "category": "Quality & Certification", "days_required": 4, "owner_team": "Risk", "is_required": True, "confidence": 0.85, "reasoning": "Risk management"},
                            {"title": "Quality Assurance Plan", "definition": "Develop QA strategy and test planning", "category": "Quality & Certification", "days_required": 5, "owner_team": "QA", "is_required": True, "confidence": 0.9, "reasoning": "Quality assurance"},
                            {"title": "Operational Readiness Plan", "definition": "Plan operations team readiness activities", "category": "Operations & Support", "days_required": 5, "owner_team": "Operations", "is_required": True, "confidence": 0.85, "reasoning": "Operations readiness"},
                            {"title": "Communication Plan", "definition": "Develop internal and external communication plan", "category": "Marketing & Communications", "days_required": 4, "owner_team": "Communications", "is_required": True, "confidence": 0.8, "reasoning": "Stakeholder engagement"},
                            {"title": "Pilot Customer Selection", "definition": "Identify and secure pilot customers for early access", "category": "Sales Enablement", "days_required": 5, "owner_team": "Sales", "is_required": True, "confidence": 0.85, "reasoning": "Validation"},
                            {"title": "Plan Phase Gate Preparation", "definition": "Prepare materials for plan phase exit review", "category": "Product Management", "days_required": 2, "owner_team": "Product", "is_required": True, "confidence": 0.95, "reasoning": "Phase exit requirement"}
                        ]
                    },
                    {
                        "phase": "develop",
                        "target_duration_days": 42,
                        "tasks": [
                            {"title": "Core Platform Development", "definition": "Build core platform capabilities", "category": "Engineering & Technical", "days_required": 30, "owner_team": "Engineering", "is_required": True, "confidence": 0.9, "reasoning": "Core delivery"},
                            {"title": "Integration Development", "definition": "Develop integrations with partner systems", "category": "Engineering & Technical", "days_required": 15, "owner_team": "Integration", "is_required": True, "confidence": 0.85, "reasoning": "Integration capability"},
                            {"title": "Sales Playbook Creation", "definition": "Create sales playbooks and battle cards", "category": "Sales Enablement", "days_required": 10, "owner_team": "Sales Ops", "is_required": True, "confidence": 0.9, "reasoning": "Sales effectiveness"},
                            {"title": "Demo Environment Setup", "definition": "Build and configure demonstration environment", "category": "Sales Enablement", "days_required": 7, "owner_team": "Sales Engineering", "is_required": True, "confidence": 0.85, "reasoning": "Sales support"},
                            {"title": "Marketing Collateral Development", "definition": "Create marketing materials and content", "category": "Marketing & Communications", "days_required": 15, "owner_team": "Marketing", "is_required": True, "confidence": 0.9, "reasoning": "Go-to-market"},
                            {"title": "Training Content Creation", "definition": "Develop training materials for all audiences", "category": "Training & Documentation", "days_required": 12, "owner_team": "Training", "is_required": True, "confidence": 0.85, "reasoning": "Enablement"},
                            {"title": "Partner Certification Program", "definition": "Build partner certification program and materials", "category": "Partner & Ecosystem", "days_required": 10, "owner_team": "Partnerships", "is_required": False, "confidence": 0.75, "reasoning": "Partner enablement"},
                            {"title": "Documentation Development", "definition": "Create user documentation and API references", "category": "Training & Documentation", "days_required": 10, "owner_team": "Documentation", "is_required": True, "confidence": 0.9, "reasoning": "Customer success"},
                            {"title": "Security Implementation", "definition": "Implement security controls and compliance requirements", "category": "Engineering & Technical", "days_required": 12, "owner_team": "Security", "is_required": True, "confidence": 0.9, "reasoning": "Security compliance"},
                            {"title": "Support Tools Configuration", "definition": "Configure support tools and knowledge base", "category": "Operations & Support", "days_required": 8, "owner_team": "Support", "is_required": True, "confidence": 0.85, "reasoning": "Support readiness"},
                            {"title": "Billing Integration", "definition": "Integrate with billing and invoicing systems", "category": "Finance & Pricing", "days_required": 8, "owner_team": "Finance IT", "is_required": True, "confidence": 0.8, "reasoning": "Revenue operations"},
                            {"title": "Quality Assurance Testing", "definition": "Execute comprehensive QA testing", "category": "Quality & Certification", "days_required": 15, "owner_team": "QA", "is_required": True, "confidence": 0.95, "reasoning": "Quality assurance"},
                            {"title": "Performance Testing", "definition": "Conduct load and performance testing", "category": "Quality & Certification", "days_required": 7, "owner_team": "QA", "is_required": True, "confidence": 0.9, "reasoning": "Performance validation"},
                            {"title": "Security Audit", "definition": "Conduct security audit and penetration testing", "category": "Quality & Certification", "days_required": 10, "owner_team": "Security", "is_required": True, "confidence": 0.9, "reasoning": "Security validation"},
                            {"title": "Pilot Customer Onboarding", "definition": "Onboard pilot customers and gather feedback", "category": "Operations & Support", "days_required": 14, "owner_team": "Customer Success", "is_required": True, "confidence": 0.9, "reasoning": "Validation"},
                            {"title": "Operations Runbook Development", "definition": "Create operational runbooks and procedures", "category": "Operations & Support", "days_required": 8, "owner_team": "Operations", "is_required": True, "confidence": 0.85, "reasoning": "Operational readiness"},
                            {"title": "Compliance Certification", "definition": "Complete required compliance certifications", "category": "Legal & Compliance", "days_required": 15, "owner_team": "Compliance", "is_required": True, "confidence": 0.85, "reasoning": "Compliance requirement"},
                            {"title": "Develop Phase Gate Preparation", "definition": "Prepare materials for develop phase exit review", "category": "Product Management", "days_required": 2, "owner_team": "Product", "is_required": True, "confidence": 0.95, "reasoning": "Phase exit requirement"}
                        ]
                    },
                    {
                        "phase": "launch",
                        "target_duration_days": 21,
                        "tasks": [
                            {"title": "Sales Team Training", "definition": "Conduct sales team training and certification", "category": "Sales Enablement", "days_required": 5, "owner_team": "Sales Ops", "is_required": True, "confidence": 0.95, "reasoning": "Sales readiness"},
                            {"title": "Support Team Training", "definition": "Train support team on new offering", "category": "Operations & Support", "days_required": 5, "owner_team": "Support", "is_required": True, "confidence": 0.9, "reasoning": "Support readiness"},
                            {"title": "Partner Launch Enablement", "definition": "Enable partners for launch", "category": "Partner & Ecosystem", "days_required": 5, "owner_team": "Partnerships", "is_required": False, "confidence": 0.75, "reasoning": "Partner readiness"},
                            {"title": "Marketing Launch Campaign", "definition": "Execute launch marketing campaign", "category": "Marketing & Communications", "days_required": 10, "owner_team": "Marketing", "is_required": True, "confidence": 0.9, "reasoning": "Demand generation"},
                            {"title": "Press and Analyst Briefings", "definition": "Conduct press and analyst briefings", "category": "Marketing & Communications", "days_required": 5, "owner_team": "Communications", "is_required": True, "confidence": 0.85, "reasoning": "Market awareness"},
                            {"title": "Customer Announcement", "definition": "Announce to existing customers", "category": "Marketing & Communications", "days_required": 3, "owner_team": "Customer Marketing", "is_required": True, "confidence": 0.9, "reasoning": "Customer awareness"},
                            {"title": "Internal Launch Communication", "definition": "Communicate launch internally across organization", "category": "Marketing & Communications", "days_required": 2, "owner_team": "Internal Comms", "is_required": True, "confidence": 0.9, "reasoning": "Internal alignment"},
                            {"title": "Production Environment Deployment", "definition": "Deploy to production environment", "category": "Engineering & Technical", "days_required": 3, "owner_team": "DevOps", "is_required": True, "confidence": 0.95, "reasoning": "Go-live"},
                            {"title": "Operations Handoff", "definition": "Complete handoff to operations team", "category": "Operations & Support", "days_required": 3, "owner_team": "Operations", "is_required": True, "confidence": 0.9, "reasoning": "Operational transition"},
                            {"title": "Monitoring and Alerting Setup", "definition": "Configure production monitoring and alerting", "category": "Engineering & Technical", "days_required": 3, "owner_team": "DevOps", "is_required": True, "confidence": 0.9, "reasoning": "Operational visibility"},
                            {"title": "Launch Readiness Review", "definition": "Conduct final launch readiness review", "category": "Product Management", "days_required": 1, "owner_team": "Product", "is_required": True, "confidence": 0.95, "reasoning": "Go/no-go decision"},
                            {"title": "Go-Live Execution", "definition": "Execute go-live activities", "category": "Product Management", "days_required": 1, "owner_team": "Product", "is_required": True, "confidence": 0.95, "reasoning": "Launch"},
                            {"title": "Post-Launch Monitoring", "definition": "Intensive monitoring during launch period", "category": "Operations & Support", "days_required": 7, "owner_team": "Operations", "is_required": True, "confidence": 0.9, "reasoning": "Launch stability"},
                            {"title": "Launch Phase Gate Preparation", "definition": "Prepare materials for launch phase exit review", "category": "Product Management", "days_required": 2, "owner_team": "Product", "is_required": True, "confidence": 0.95, "reasoning": "Phase exit requirement"}
                        ]
                    },
                    {
                        "phase": "sustain",
                        "target_duration_days": 30,
                        "tasks": [
                            {"title": "Performance KPI Tracking", "definition": "Establish and track performance KPIs", "category": "Operations & Support", "days_required": 5, "owner_team": "Operations", "is_required": True, "confidence": 0.9, "reasoning": "Performance management"},
                            {"title": "Customer Feedback Loop", "definition": "Establish systematic customer feedback collection", "category": "Product Management", "days_required": 5, "owner_team": "Product", "is_required": True, "confidence": 0.9, "reasoning": "Continuous improvement"},
                            {"title": "Continuous Improvement Process", "definition": "Implement continuous improvement process", "category": "Quality & Certification", "days_required": 5, "owner_team": "Quality", "is_required": True, "confidence": 0.85, "reasoning": "Optimization"},
                            {"title": "Regular Business Reviews", "definition": "Establish cadence for business performance reviews", "category": "Finance & Pricing", "days_required": 3, "owner_team": "Finance", "is_required": True, "confidence": 0.85, "reasoning": "Business health"},
                            {"title": "Customer Success Reviews", "definition": "Conduct regular customer success reviews", "category": "Operations & Support", "days_required": 5, "owner_team": "Customer Success", "is_required": True, "confidence": 0.9, "reasoning": "Customer retention"},
                            {"title": "Roadmap Planning", "definition": "Plan future enhancements and roadmap", "category": "Product Management", "days_required": 7, "owner_team": "Product", "is_required": True, "confidence": 0.85, "reasoning": "Future development"},
                            {"title": "Competitive Monitoring", "definition": "Monitor competitive landscape and respond", "category": "Product Management", "days_required": 3, "owner_team": "Product", "is_required": True, "confidence": 0.8, "reasoning": "Market position"},
                            {"title": "Operational Optimization", "definition": "Optimize operational processes based on learnings", "category": "Operations & Support", "days_required": 7, "owner_team": "Operations", "is_required": True, "confidence": 0.85, "reasoning": "Efficiency"},
                            {"title": "Training Refresh", "definition": "Update training materials based on feedback", "category": "Training & Documentation", "days_required": 5, "owner_team": "Training", "is_required": False, "confidence": 0.75, "reasoning": "Enablement maintenance"},
                            {"title": "Documentation Updates", "definition": "Maintain and update documentation", "category": "Training & Documentation", "days_required": 5, "owner_team": "Documentation", "is_required": True, "confidence": 0.8, "reasoning": "Customer success"}
                        ]
                    }
                ],
                "offer_type": "Professional Services",
                "complexity_assessment": "medium",
                "total_estimated_days": 170,
                "key_risks": [
                    "Resource availability during develop phase",
                    "Partner certification timeline dependencies",
                    "Compliance certification delays",
                    "Pilot customer availability"
                ]
            }
            return None, [{"name": "generate_offer_lifecycle_tasks", "arguments": json.dumps(sample_lifecycle)}]

        # Default: return sample work breakdown for PRD analysis
        sample_breakdown = {
            "epics": [
                {
                    "title": "Sample Epic",
                    "description": "This is a sample epic generated by the stub LLM.",
                    "priority": "high",
                    "stories": [
                        {
                            "title": "Sample Story 1",
                            "description": "As a user, I want sample functionality.",
                            "acceptance_criteria": "- Criteria 1\n- Criteria 2",
                            "story_points": 5,
                            "estimated_hours": 8,
                            "priority": "high",
                            "tasks": [
                                {"title": "Implement feature", "description": "Implement the core feature", "estimated_hours": 4},
                                {"title": "Write tests", "description": "Write unit tests", "estimated_hours": 2},
                                {"title": "Documentation", "description": "Update documentation", "estimated_hours": 2},
                            ],
                        },
                        {
                            "title": "Sample Story 2",
                            "description": "As a user, I want more sample functionality.",
                            "acceptance_criteria": "- Criteria A\n- Criteria B",
                            "story_points": 3,
                            "estimated_hours": 5,
                            "priority": "medium",
                            "tasks": [
                                {"title": "Design component", "description": "Design the UI component", "estimated_hours": 2},
                                {"title": "Implement component", "description": "Build the component", "estimated_hours": 3},
                            ],
                        },
                    ],
                }
            ]
        }
        return None, [{"name": "create_work_breakdown", "arguments": json.dumps(sample_breakdown)}]


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI LLM provider."""

    def __init__(self, db: Optional[Session] = None):
        from openai import AsyncAzureOpenAI

        # Read from database first, fall back to environment
        api_key = get_db_setting(db, "azure_openai_api_key", settings.azure_openai_api_key)
        endpoint = get_db_setting(db, "azure_openai_endpoint", settings.azure_openai_endpoint)
        deployment = get_db_setting(db, "azure_openai_deployment", settings.azure_openai_deployment)
        api_version = settings.azure_openai_api_version

        if not api_key or not endpoint:
            raise ValueError("Azure OpenAI API key and endpoint must be configured")

        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint,
        )
        self.deployment = deployment

    async def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        kwargs = {"model": self.deployment, "messages": messages}
        if tools:
            kwargs["tools"] = tools

        response = await self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        return {
            "content": message.content,
            "tool_calls": (
                [
                    {"name": tc.function.name, "arguments": tc.function.arguments}
                    for tc in message.tool_calls
                ]
                if message.tool_calls
                else None
            ),
        }

    async def complete_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> tuple[str | None, list[dict] | None]:
        result = await self.complete(messages, tools)
        return result["content"], result["tool_calls"]


def get_llm_provider(db: Optional[Session] = None) -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    # Check database setting first, fall back to environment
    provider = get_db_setting(db, "llm_provider", settings.llm_provider)

    if provider == "azure_openai":
        return AzureOpenAIProvider(db)
    return StubLLMProvider()
