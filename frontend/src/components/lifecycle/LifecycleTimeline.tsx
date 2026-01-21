import { CheckCircle, Circle, Clock, AlertCircle, ChevronRight, Lock } from 'lucide-react';
import type { OfferLifecyclePhase, PhaseStatus } from '../../types';

interface LifecycleTimelineProps {
  phases: OfferLifecyclePhase[];
  selectedPhaseId: number | null;
  onPhaseSelect: (phase: OfferLifecyclePhase) => void;
}

const PHASE_LABELS: Record<string, string> = {
  concept: 'Concept',
  define: 'Define',
  plan: 'Plan',
  develop: 'Develop',
  launch: 'Launch',
  sustain: 'Sustain',
};

const STATUS_CONFIG: Record<PhaseStatus, { color: string; bgColor: string; icon: typeof Circle }> = {
  not_started: { color: 'text-gray-400', bgColor: 'bg-gray-100', icon: Circle },
  in_progress: { color: 'text-blue-600', bgColor: 'bg-blue-100', icon: Clock },
  pending_approval: { color: 'text-yellow-600', bgColor: 'bg-yellow-100', icon: AlertCircle },
  approved: { color: 'text-green-600', bgColor: 'bg-green-100', icon: CheckCircle },
  skipped: { color: 'text-gray-500', bgColor: 'bg-gray-200', icon: Lock },
};

export function LifecycleTimeline({ phases, selectedPhaseId, onPhaseSelect }: LifecycleTimelineProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Offer Lifecycle</h2>

      <div className="flex items-center justify-between">
        {phases.map((phase, index) => {
          const config = STATUS_CONFIG[phase.status];
          const Icon = config.icon;
          const isSelected = phase.id === selectedPhaseId;
          const progress = phase.task_count > 0
            ? Math.round((phase.completed_task_count / phase.task_count) * 100)
            : 0;

          return (
            <div key={phase.id} className="flex items-center flex-1">
              <button
                onClick={() => onPhaseSelect(phase)}
                className={`
                  flex flex-col items-center p-3 rounded-lg transition-all flex-1
                  ${isSelected ? 'bg-blue-50 ring-2 ring-blue-500' : 'hover:bg-gray-50'}
                `}
              >
                <div className={`
                  w-10 h-10 rounded-full flex items-center justify-center mb-2
                  ${config.bgColor}
                `}>
                  <Icon className={`w-5 h-5 ${config.color}`} />
                </div>

                <span className={`text-sm font-medium ${isSelected ? 'text-blue-700' : 'text-gray-700'}`}>
                  {PHASE_LABELS[phase.phase]}
                </span>

                <span className="text-xs text-gray-500 mt-1">
                  {phase.completed_task_count}/{phase.task_count} tasks
                </span>

                {phase.task_count > 0 && (
                  <div className="w-full mt-2">
                    <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          phase.status === 'approved' ? 'bg-green-500' :
                          phase.status === 'in_progress' ? 'bg-blue-500' :
                          phase.status === 'pending_approval' ? 'bg-yellow-500' :
                          'bg-gray-300'
                        }`}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                )}

                {phase.sequence_overridden && (
                  <span className="text-xs text-orange-600 mt-1">Overridden</span>
                )}
              </button>

              {index < phases.length - 1 && (
                <ChevronRight className="w-5 h-5 text-gray-300 mx-1 flex-shrink-0" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
