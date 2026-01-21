export interface Project {
  id: number;
  name: string;
  description: string | null;
  prd_content: string;
  status: 'draft' | 'analyzing' | 'ready' | 'in_progress' | 'completed';
  epics?: Epic[];
  total_story_points?: number;
  total_estimated_hours?: number;
}

export interface Epic {
  id: number;
  project_id: number;
  title: string;
  description: string | null;
  priority: Priority;
  order: number;
  stories?: Story[];
}

export interface Story {
  id: number;
  epic_id: number;
  sprint_id: number | null;
  title: string;
  description: string | null;
  acceptance_criteria: string | null;
  story_points: number | null;
  estimated_hours: number | null;
  priority: Priority;
  status: StoryStatus;
  order: number;
  tasks?: Task[];
}

export interface Task {
  id: number;
  story_id: number;
  title: string;
  description: string | null;
  estimated_hours: number | null;
  status: TaskStatus;
  order: number;
}

export interface Sprint {
  id: number;
  project_id: number;
  name: string;
  goal: string | null;
  start_date: string | null;
  end_date: string | null;
  capacity_hours: number | null;
  status: SprintStatus;
  order: number;
  stories: Story[];
  total_points?: number;
  total_hours?: number;
}

export interface TeamMember {
  id: number;
  project_id: number;
  name: string;
  email: string | null;
  role: string | null;
  hours_per_sprint: number;
}

export type Priority = 'low' | 'medium' | 'high' | 'critical';
export type StoryStatus = 'backlog' | 'ready' | 'in_progress' | 'in_review' | 'done';
export type TaskStatus = 'todo' | 'in_progress' | 'done';
export type SprintStatus = 'planning' | 'active' | 'completed';

// Offer Lifecycle Types
export type LifecyclePhase = 'concept' | 'define' | 'plan' | 'develop' | 'launch' | 'sustain';
export type PhaseStatus = 'not_started' | 'in_progress' | 'pending_approval' | 'approved' | 'skipped';
export type ServiceTaskStatus = 'not_started' | 'in_progress' | 'blocked' | 'completed' | 'deferred' | 'not_applicable';
export type TaskSource = 'ai_generated' | 'template' | 'manual';

export interface OfferLifecyclePhase {
  id: number;
  project_id: number;
  phase: LifecyclePhase;
  status: PhaseStatus;
  order: number;
  approval_required: boolean;
  approved_by: string | null;
  approved_at: string | null;
  approval_notes: string | null;
  sequence_overridden: boolean;
  override_reason: string | null;
  target_start_date: string | null;
  target_end_date: string | null;
  actual_start_date: string | null;
  actual_end_date: string | null;
  task_count: number;
  completed_task_count: number;
}

export interface ServiceTask {
  id: number;
  phase_id: number;
  title: string;
  description: string | null;
  definition: string | null;
  category: string | null;
  subcategory: string | null;
  status: ServiceTaskStatus;
  source: TaskSource;
  target_start_date: string | null;
  target_complete_date: string | null;
  days_required: number | null;
  actual_start_date: string | null;
  actual_complete_date: string | null;
  owner: string | null;
  team: string | null;
  linked_epic_id: number | null;
  linked_story_id: number | null;
  order: number;
  is_required: boolean;
  notes: string | null;
  completion_notes: string | null;
}

export interface LifecycleSummary {
  project_id: number;
  total_tasks: number;
  completed_tasks: number;
  phases: OfferLifecyclePhase[];
  current_phase: LifecyclePhase | null;
  overall_progress: number;
  estimated_completion_date: string | null;
}
