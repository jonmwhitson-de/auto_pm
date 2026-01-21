import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, RefreshCw, Trash2, Loader2, AlertCircle } from 'lucide-react';
import {
  getProject,
  getLifecycleSummary,
  analyzeLifecycle,
  deleteLifecycle,
  getPhaseTasks,
  startPhase,
  submitPhaseForApproval,
  approvePhase,
  overridePhase,
  updateServiceTask,
} from '../api/client';
import { LifecycleTimeline } from '../components/lifecycle/LifecycleTimeline';
import { PhaseDetailPanel } from '../components/lifecycle/PhaseDetailPanel';
import { ServiceTaskList } from '../components/lifecycle/ServiceTaskList';
import type { OfferLifecyclePhase, ServiceTask, ServiceTaskStatus } from '../types';

export function LifecyclePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [selectedPhase, setSelectedPhase] = useState<OfferLifecyclePhase | null>(null);

  const projectIdNum = parseInt(projectId || '0', 10);

  // Fetch project
  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectIdNum],
    queryFn: () => getProject(projectIdNum),
    enabled: projectIdNum > 0,
  });

  // Fetch lifecycle summary
  const {
    data: lifecycleSummary,
    isLoading: lifecycleLoading,
    error: lifecycleError,
  } = useQuery({
    queryKey: ['lifecycle', projectIdNum],
    queryFn: () => getLifecycleSummary(projectIdNum),
    enabled: projectIdNum > 0,
    retry: false,
  });

  // Fetch tasks for selected phase
  const { data: phaseTasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['lifecycle-tasks', selectedPhase?.id],
    queryFn: () => getPhaseTasks(selectedPhase!.id),
    enabled: !!selectedPhase,
  });

  // Analyze lifecycle mutation
  const analyzeMutation = useMutation({
    mutationFn: () => analyzeLifecycle(projectIdNum),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lifecycle', projectIdNum] });
    },
  });

  // Delete lifecycle mutation
  const deleteMutation = useMutation({
    mutationFn: () => deleteLifecycle(projectIdNum),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lifecycle', projectIdNum] });
      setSelectedPhase(null);
    },
  });

  // Phase action mutations
  const startPhaseMutation = useMutation({
    mutationFn: (phaseId: number) => startPhase(phaseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lifecycle', projectIdNum] });
    },
  });

  const submitForApprovalMutation = useMutation({
    mutationFn: (phaseId: number) => submitPhaseForApproval(phaseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lifecycle', projectIdNum] });
    },
  });

  const approvePhaseMutation = useMutation({
    mutationFn: ({ phaseId, approvedBy, notes }: { phaseId: number; approvedBy: string; notes?: string }) =>
      approvePhase(phaseId, approvedBy, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lifecycle', projectIdNum] });
    },
  });

  const overridePhaseMutation = useMutation({
    mutationFn: ({ phaseId, overriddenBy, reason }: { phaseId: number; overriddenBy: string; reason: string }) =>
      overridePhase(phaseId, overriddenBy, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lifecycle', projectIdNum] });
    },
  });

  // Task status mutation
  const updateTaskMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: number; status: ServiceTaskStatus }) =>
      updateServiceTask(taskId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lifecycle-tasks', selectedPhase?.id] });
      queryClient.invalidateQueries({ queryKey: ['lifecycle', projectIdNum] });
    },
  });

  // Update selected phase when lifecycle data changes
  if (lifecycleSummary && !selectedPhase && lifecycleSummary.phases.length > 0) {
    // Select the current in-progress phase or the first one
    const inProgressPhase = lifecycleSummary.phases.find(p => p.status === 'in_progress');
    setSelectedPhase(inProgressPhase || lifecycleSummary.phases[0]);
  }

  // Update selected phase data from lifecycle summary
  const currentSelectedPhase = selectedPhase
    ? lifecycleSummary?.phases.find(p => p.id === selectedPhase.id) || selectedPhase
    : null;

  // Check if previous phase is approved (for canStart)
  const canStartPhase = (phase: OfferLifecyclePhase) => {
    if (phase.order === 1) return true;
    const prevPhase = lifecycleSummary?.phases.find(p => p.order === phase.order - 1);
    return prevPhase?.status === 'approved';
  };

  if (projectLoading || lifecycleLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">Project not found</h2>
        <Link to="/" className="text-blue-600 hover:underline mt-2 inline-block">
          Back to projects
        </Link>
      </div>
    );
  }

  const hasLifecycle = lifecycleSummary && lifecycleSummary.phases.length > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link
            to={`/projects/${projectId}`}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
            <p className="text-sm text-gray-500">Offer Lifecycle Management</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {hasLifecycle && (
            <>
              <button
                onClick={() => {
                  if (confirm('Are you sure you want to regenerate the lifecycle? This will delete all existing phases and tasks.')) {
                    deleteMutation.mutate();
                  }
                }}
                disabled={deleteMutation.isPending}
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md"
              >
                <Trash2 className="w-4 h-4 mr-1" />
                Delete Lifecycle
              </button>
            </>
          )}
        </div>
      </div>

      {/* No lifecycle yet */}
      {!hasLifecycle && lifecycleError && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Lifecycle Generated</h2>
          <p className="text-gray-600 mb-6">
            Analyze the PRD to generate an Offer Lifecycle with Services-focused tasks.
          </p>
          <button
            onClick={() => analyzeMutation.mutate()}
            disabled={analyzeMutation.isPending}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50"
          >
            {analyzeMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Analyzing PRD...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Generate Offer Lifecycle
              </>
            )}
          </button>
        </div>
      )}

      {/* Lifecycle exists */}
      {hasLifecycle && (
        <div className="space-y-6">
          {/* Progress Summary */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm text-gray-500">Overall Progress</span>
                <div className="flex items-center gap-3 mt-1">
                  <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 rounded-full transition-all"
                      style={{ width: `${lifecycleSummary.overall_progress}%` }}
                    />
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {Math.round(lifecycleSummary.overall_progress)}%
                  </span>
                </div>
              </div>
              <div className="text-right">
                <span className="text-sm text-gray-500">Tasks Completed</span>
                <p className="text-lg font-semibold text-gray-900">
                  {lifecycleSummary.completed_tasks} / {lifecycleSummary.total_tasks}
                </p>
              </div>
              {lifecycleSummary.estimated_completion_date && (
                <div className="text-right">
                  <span className="text-sm text-gray-500">Est. Completion</span>
                  <p className="text-lg font-semibold text-gray-900">
                    {new Date(lifecycleSummary.estimated_completion_date).toLocaleDateString()}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Timeline */}
          <LifecycleTimeline
            phases={lifecycleSummary.phases}
            selectedPhaseId={currentSelectedPhase?.id || null}
            onPhaseSelect={setSelectedPhase}
          />

          {/* Phase Detail and Tasks */}
          {currentSelectedPhase && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <PhaseDetailPanel
                  phase={currentSelectedPhase}
                  canStart={canStartPhase(currentSelectedPhase)}
                  onStart={() => startPhaseMutation.mutate(currentSelectedPhase.id)}
                  onSubmitForApproval={() => submitForApprovalMutation.mutate(currentSelectedPhase.id)}
                  onApprove={(approvedBy, notes) =>
                    approvePhaseMutation.mutate({ phaseId: currentSelectedPhase.id, approvedBy, notes })
                  }
                  onOverride={(overriddenBy, reason) =>
                    overridePhaseMutation.mutate({ phaseId: currentSelectedPhase.id, overriddenBy, reason })
                  }
                />
              </div>

              <div className="lg:col-span-2">
                {tasksLoading ? (
                  <div className="flex items-center justify-center h-64 bg-white rounded-lg shadow">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                  </div>
                ) : (
                  <ServiceTaskList
                    tasks={phaseTasks || []}
                    onTaskStatusChange={(taskId, status) =>
                      updateTaskMutation.mutate({ taskId, status })
                    }
                    onTaskClick={(task) => {
                      // Could open a detail modal here
                      console.log('Task clicked:', task);
                    }}
                    onAddTask={() => {
                      // Could open an add task modal here
                      console.log('Add task clicked');
                    }}
                  />
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
