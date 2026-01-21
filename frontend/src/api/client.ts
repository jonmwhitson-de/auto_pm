import axios from 'axios';
import type { Project, Sprint, TeamMember } from '../types';

const api = axios.create({
  baseURL: '/api',
});

// Projects
export const getProjects = () => api.get<Project[]>('/projects').then(res => res.data);

export const getProject = (id: number) =>
  api.get<Project>(`/projects/${id}`).then(res => res.data);

export const createProject = (data: { name: string; description?: string; prd_content: string }) =>
  api.post<Project>('/projects', data).then(res => res.data);

export const uploadProject = (formData: FormData) =>
  api.post<Project>('/projects/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(res => res.data);

export const deleteProject = (id: number) =>
  api.delete(`/projects/${id}`).then(res => res.data);

// Analysis
export const analyzeProject = (projectId: number) =>
  api.post('/analyze', { project_id: projectId }).then(res => res.data);

// Sprints
export const getSprints = (projectId: number) =>
  api.get<Sprint[]>(`/sprints/project/${projectId}`).then(res => res.data);

export const createSprint = (data: {
  project_id: number;
  name: string;
  goal?: string;
  start_date?: string;
  end_date?: string;
  capacity_hours?: number;
}) => api.post<Sprint>('/sprints', data).then(res => res.data);

export const planSprint = (sprintId: number, storyIds: number[]) =>
  api.post('/sprints/plan', { sprint_id: sprintId, story_ids: storyIds }).then(res => res.data);

export const deleteSprint = (id: number) =>
  api.delete(`/sprints/${id}`).then(res => res.data);

// Team Members
export const getTeamMembers = (projectId: number) =>
  api.get<TeamMember[]>(`/team-members/project/${projectId}`).then(res => res.data);

export const createTeamMember = (data: {
  project_id: number;
  name: string;
  email?: string;
  role?: string;
  hours_per_sprint?: number;
}) => api.post<TeamMember>('/team-members', data).then(res => res.data);

export const deleteTeamMember = (id: number) =>
  api.delete(`/team-members/${id}`).then(res => res.data);

export const getTeamCapacity = (projectId: number) =>
  api.get(`/team-members/project/${projectId}/capacity`).then(res => res.data);

// Stories
export const updateStory = (storyId: number, data: Partial<{
  sprint_id: number | null;
  status: string;
  priority: string;
}>) => api.patch(`/stories/${storyId}`, data).then(res => res.data);

// Admin - LLM Config
export interface LLMConfig {
  provider: string;
  azure_endpoint: string | null;
  azure_deployment: string;
  azure_api_version: string;
  has_api_key: boolean;
}

export const getLLMConfig = () =>
  api.get<LLMConfig>('/admin/llm-config').then(res => res.data);

export const updateLLMConfig = (data: {
  provider?: string;
  azure_endpoint?: string;
  azure_deployment?: string;
  azure_api_key?: string;
}) => api.patch<LLMConfig>('/admin/llm-config', data).then(res => res.data);

// Admin - MCP Tools
export interface MCPTool {
  id: number;
  name: string;
  description: string | null;
  enabled: boolean;
  config: Record<string, unknown> | null;
}

export const getTools = () =>
  api.get<MCPTool[]>('/admin/tools').then(res => res.data);

export const updateTool = (toolId: number, data: { enabled?: boolean; config?: Record<string, unknown> }) =>
  api.patch<MCPTool>(`/admin/tools/${toolId}`, data).then(res => res.data);

// Admin - Integrations
export interface Integration {
  id: number;
  name: string;
  display_name: string;
  enabled: boolean;
  status: string;
  last_sync: string | null;
  config_keys: string[];
}

export const getIntegrations = () =>
  api.get<Integration[]>('/admin/integrations').then(res => res.data);

export const updateIntegration = (integrationId: number, data: { enabled?: boolean; config?: Record<string, string> }) =>
  api.patch<Integration>(`/admin/integrations/${integrationId}`, data).then(res => res.data);

export const testIntegration = (integrationId: number) =>
  api.post<{ success: boolean; message: string }>(`/admin/integrations/${integrationId}/test`).then(res => res.data);

// ============ Intake ============

export interface IntakeSummary {
  id: number;
  title: string;
  source: string;
  inferred_type: string | null;
  type_confidence: number | null;
  priority_score: number | null;
  status: string;
  received_at: string;
  missing_info_count: number;
  blocking_questions_count: number;
  has_pm_brief: boolean;
}

export interface PMBrief {
  problem_statement: string | null;
  target_users: string[];
  use_cases: string[];
  north_star_metric: string | null;
  input_metrics: string[];
  security_constraints: string | null;
  privacy_constraints: string | null;
  performance_constraints: string | null;
  budget_constraints: string | null;
  compatibility_constraints: string | null;
  assumptions: string[];
  out_of_scope: string[];
  acceptance_criteria: string[];
  team_dependencies: string[];
  service_dependencies: string[];
  vendor_dependencies: string[];
  missing_fields: string[];
  extraction_confidence: number;
}

export interface ClarifyingQuestion {
  id: number;
  question: string;
  context: string | null;
  target_field: string | null;
  assigned_to: string | null;
  priority: number;
  is_blocking: boolean;
  is_answered: boolean;
  answer: string | null;
}

export interface IntakeStakeholder {
  id: number;
  name: string;
  role: string | null;
  influence: string;
  interest: string;
}

export interface IntakeDetail {
  id: number;
  title: string;
  raw_content: string;
  source: string;
  source_url: string | null;
  source_author: string | null;
  inferred_type: string | null;
  type_confidence: number | null;
  priority_score: number | null;
  priority_rationale: string | null;
  status: string;
  duplicate_of_id: number | null;
  duplicate_confidence: number | null;
  converted_to_project_id: number | null;
  received_at: string;
  pm_brief: PMBrief | null;
  clarifying_questions: ClarifyingQuestion[];
  stakeholders: IntakeStakeholder[];
}

export interface IntakeStats {
  total: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  needs_attention: number;
}

export const getIntakes = (status?: string) =>
  api.get<IntakeSummary[]>('/intake', { params: status ? { status } : {} }).then(res => res.data);

export const getIntake = (id: number) =>
  api.get<IntakeDetail>(`/intake/${id}`).then(res => res.data);

export const createIntake = (data: {
  title: string;
  raw_content: string;
  source?: string;
  source_author?: string;
  source_url?: string;
}) => api.post<IntakeSummary>('/intake', data).then(res => res.data);

export const processIntake = (id: number) =>
  api.post(`/intake/${id}/process`).then(res => res.data);

export const convertIntakeToProject = (id: number) =>
  api.post<{ message: string; project_id: number }>(`/intake/${id}/convert`).then(res => res.data);

export const answerQuestion = (intakeId: number, questionId: number, answer: string, answeredBy?: string) =>
  api.post(`/intake/${intakeId}/questions/${questionId}/answer`, { answer, answered_by: answeredBy }).then(res => res.data);

export const updateIntakeStatus = (id: number, status: string) =>
  api.patch(`/intake/${id}/status`, null, { params: { status } }).then(res => res.data);

export const mergeIntakes = (intakeId: number, duplicateId: number) =>
  api.post(`/intake/${intakeId}/merge/${duplicateId}`).then(res => res.data);

export const deleteIntake = (id: number) =>
  api.delete(`/intake/${id}`).then(res => res.data);

export const getIntakeStats = () =>
  api.get<IntakeStats>('/intake/stats/summary').then(res => res.data);

// ============ Planning ============

export interface Dependency {
  id: number;
  project_id: number;
  source_type: string;
  source_id: number;
  target_type: string;
  target_id: number;
  dependency_type: string;
  status: string;
  inferred: boolean;
  confidence: number | null;
  inference_reason: string | null;
  notes: string | null;
  created_at: string;
}

export interface Decision {
  id: number;
  project_id: number;
  title: string;
  context: string | null;
  decision: string;
  rationale: string | null;
  alternatives: string | null;
  consequences: string | null;
  status: string;
  decision_maker: string | null;
  decision_date: string | null;
  extracted_from: string | null;
  created_at: string;
}

export interface Assumption {
  id: number;
  project_id: number;
  assumption: string;
  context: string | null;
  impact_if_wrong: string | null;
  status: string;
  risk_level: string;
  validation_method: string | null;
  validation_owner: string | null;
  validation_deadline: string | null;
  validation_result: string | null;
  validated_at: string | null;
  extracted_from: string | null;
  created_at: string;
}

export interface StoryEstimate {
  id: number;
  story_id: number;
  estimate_p10: number | null;
  estimate_p50: number | null;
  estimate_p90: number | null;
  rice_score: number | null;
  wsjf_score: number | null;
  ai_estimate_p10: number | null;
  ai_estimate_p50: number | null;
  ai_estimate_p90: number | null;
  ai_confidence: number | null;
  ai_reasoning: string | null;
}

export interface CriticalPathItem {
  item: string;
  duration: number;
  total_duration: number;
}

export interface PrioritizedStory {
  id: number;
  title: string;
  epic_id: number;
  epic_title: string;
  story_points: number | null;
  estimated_hours: number | null;
  rice_score: number | null;
  wsjf_score: number | null;
  estimate_p50: number | null;
  priority_score: number | null;
}

// Dependencies
export const getDependencies = (projectId: number, status?: string) =>
  api.get<Dependency[]>(`/planning/projects/${projectId}/dependencies`, { params: status ? { status } : {} }).then(res => res.data);

export const createDependency = (projectId: number, data: {
  source_type: string;
  source_id: number;
  target_type: string;
  target_id: number;
  dependency_type?: string;
  notes?: string;
}) => api.post<Dependency>(`/planning/projects/${projectId}/dependencies`, data).then(res => res.data);

export const updateDependency = (dependencyId: number, data: {
  status?: string;
  notes?: string;
}) => api.put<Dependency>(`/planning/dependencies/${dependencyId}`, data).then(res => res.data);

export const deleteDependency = (dependencyId: number) =>
  api.delete(`/planning/dependencies/${dependencyId}`).then(res => res.data);

export const inferDependencies = (projectId: number) =>
  api.post<Dependency[]>(`/planning/projects/${projectId}/dependencies/infer`).then(res => res.data);

export const getCriticalPath = (projectId: number) =>
  api.get<CriticalPathItem[]>(`/planning/projects/${projectId}/critical-path`).then(res => res.data);

// Decisions
export const getDecisions = (projectId: number, status?: string) =>
  api.get<Decision[]>(`/planning/projects/${projectId}/decisions`, { params: status ? { status } : {} }).then(res => res.data);

export const createDecision = (projectId: number, data: {
  title: string;
  context?: string;
  decision: string;
  rationale?: string;
  alternatives?: string[];
  consequences?: string;
  decision_maker?: string;
}) => api.post<Decision>(`/planning/projects/${projectId}/decisions`, data).then(res => res.data);

export const updateDecision = (decisionId: number, data: {
  title?: string;
  context?: string;
  decision?: string;
  rationale?: string;
  alternatives?: string[];
  consequences?: string;
  status?: string;
  decision_maker?: string;
}) => api.put<Decision>(`/planning/decisions/${decisionId}`, data).then(res => res.data);

export const deleteDecision = (decisionId: number) =>
  api.delete(`/planning/decisions/${decisionId}`).then(res => res.data);

// Assumptions
export const getAssumptions = (projectId: number, status?: string, riskLevel?: string) =>
  api.get<Assumption[]>(`/planning/projects/${projectId}/assumptions`, {
    params: { ...(status ? { status } : {}), ...(riskLevel ? { risk_level: riskLevel } : {}) }
  }).then(res => res.data);

export const createAssumption = (projectId: number, data: {
  assumption: string;
  context?: string;
  impact_if_wrong?: string;
  risk_level?: string;
  validation_method?: string;
  validation_owner?: string;
  validation_deadline?: string;
}) => api.post<Assumption>(`/planning/projects/${projectId}/assumptions`, data).then(res => res.data);

export const updateAssumption = (assumptionId: number, data: {
  assumption?: string;
  context?: string;
  impact_if_wrong?: string;
  status?: string;
  risk_level?: string;
  validation_method?: string;
  validation_owner?: string;
  validation_deadline?: string;
  validation_result?: string;
}) => api.put<Assumption>(`/planning/assumptions/${assumptionId}`, data).then(res => res.data);

export const deleteAssumption = (assumptionId: number) =>
  api.delete(`/planning/assumptions/${assumptionId}`).then(res => res.data);

// AI Extraction
export const extractPlanningItems = (projectId: number, content: string, source?: string) =>
  api.post<{
    decisions_extracted: number;
    assumptions_extracted: number;
    decisions: Decision[];
    assumptions: Assumption[];
  }>(`/planning/projects/${projectId}/extract-planning`, { content, source: source || 'manual' }).then(res => res.data);

// Story Estimates
export const getStoryEstimate = (storyId: number) =>
  api.get<StoryEstimate>(`/planning/stories/${storyId}/estimate`).then(res => res.data);

export const generateStoryEstimate = (storyId: number) =>
  api.post<StoryEstimate>(`/planning/stories/${storyId}/estimate/generate`).then(res => res.data);

export const setRICEScores = (storyId: number, scores: {
  reach: number;
  impact: number;
  confidence: number;
  effort: number;
}) => api.put<StoryEstimate>(`/planning/stories/${storyId}/estimate/rice`, scores).then(res => res.data);

export const setWSJFScores = (storyId: number, scores: {
  business_value: number;
  time_criticality: number;
  risk_reduction: number;
  job_size: number;
}) => api.put<StoryEstimate>(`/planning/stories/${storyId}/estimate/wsjf`, scores).then(res => res.data);

export const setRangeEstimate = (storyId: number, data: {
  p10: number;
  p50: number;
  p90: number;
}) => api.put<StoryEstimate>(`/planning/stories/${storyId}/estimate/range`, data).then(res => res.data);

// Prioritized Backlog
export const getPrioritizedBacklog = (projectId: number, model: 'rice' | 'wsjf' = 'rice') =>
  api.get<{ model: string; stories: PrioritizedStory[] }>(`/planning/projects/${projectId}/prioritized-backlog`, { params: { model } }).then(res => res.data);

// ============ Offer Lifecycle ============

import type { OfferLifecyclePhase, ServiceTask, LifecycleSummary } from '../types';

// Lifecycle Analysis
export const analyzeLifecycle = (projectId: number, startDate?: string) =>
  api.post<OfferLifecyclePhase[]>('/lifecycle/analyze', {
    project_id: projectId,
    start_date: startDate
  }).then(res => res.data);

export const getLifecycleSummary = (projectId: number) =>
  api.get<LifecycleSummary>(`/lifecycle/projects/${projectId}`).then(res => res.data);

export const deleteLifecycle = (projectId: number) =>
  api.delete(`/lifecycle/projects/${projectId}`).then(res => res.data);

// Phase Management
export const getPhase = (phaseId: number) =>
  api.get<OfferLifecyclePhase>(`/lifecycle/phases/${phaseId}`).then(res => res.data);

export const startPhase = (phaseId: number) =>
  api.post<OfferLifecyclePhase>(`/lifecycle/phases/${phaseId}/start`).then(res => res.data);

export const submitPhaseForApproval = (phaseId: number) =>
  api.post<OfferLifecyclePhase>(`/lifecycle/phases/${phaseId}/submit-for-approval`).then(res => res.data);

export const approvePhase = (phaseId: number, approvedBy: string, notes?: string) =>
  api.post<OfferLifecyclePhase>(`/lifecycle/phases/${phaseId}/approve`, {
    approved_by: approvedBy,
    notes
  }).then(res => res.data);

export const overridePhase = (phaseId: number, overriddenBy: string, reason: string) =>
  api.post<OfferLifecyclePhase>(`/lifecycle/phases/${phaseId}/override`, {
    overridden_by: overriddenBy,
    reason
  }).then(res => res.data);

// Service Tasks
export const getPhaseTasks = (phaseId: number, status?: string, category?: string) =>
  api.get<ServiceTask[]>(`/lifecycle/phases/${phaseId}/tasks`, {
    params: { ...(status ? { status } : {}), ...(category ? { category } : {}) }
  }).then(res => res.data);

export const createServiceTask = (phaseId: number, data: {
  title: string;
  definition?: string;
  category?: string;
  subcategory?: string;
  days_required?: number;
  target_start_date?: string;
  owner?: string;
  team?: string;
  is_required?: boolean;
}) => api.post<ServiceTask>(`/lifecycle/phases/${phaseId}/tasks`, data).then(res => res.data);

export const getServiceTask = (taskId: number) =>
  api.get<ServiceTask>(`/lifecycle/tasks/${taskId}`).then(res => res.data);

export const updateServiceTask = (taskId: number, data: Partial<{
  title: string;
  definition: string;
  status: string;
  target_start_date: string;
  target_complete_date: string;
  actual_start_date: string;
  actual_complete_date: string;
  owner: string;
  team: string;
  notes: string;
  completion_notes: string;
  linked_epic_id: number;
  linked_story_id: number;
}>) => api.put<ServiceTask>(`/lifecycle/tasks/${taskId}`, data).then(res => res.data);

export const deleteServiceTask = (taskId: number) =>
  api.delete(`/lifecycle/tasks/${taskId}`).then(res => res.data);

export const linkTaskToDevWork = (taskId: number, epicId?: number, storyId?: number) =>
  api.post<ServiceTask>(`/lifecycle/tasks/${taskId}/link-dev-work`, null, {
    params: { ...(epicId ? { epic_id: epicId } : {}), ...(storyId ? { story_id: storyId } : {}) }
  }).then(res => res.data);

export const bulkUpdateTaskStatus = (phaseId: number, taskIds: number[], status: string) =>
  api.post<{ updated: number }>(`/lifecycle/phases/${phaseId}/tasks/bulk-status`, {
    task_ids: taskIds,
    status
  }).then(res => res.data);
