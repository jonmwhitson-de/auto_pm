import { useState } from 'react';
import { Play, Send, CheckCircle, FastForward, Calendar, AlertTriangle } from 'lucide-react';
import type { OfferLifecyclePhase } from '../../types';

interface PhaseDetailPanelProps {
  phase: OfferLifecyclePhase;
  canStart: boolean;
  onStart: () => void;
  onSubmitForApproval: () => void;
  onApprove: (approvedBy: string, notes?: string) => void;
  onOverride: (overriddenBy: string, reason: string) => void;
}

const PHASE_LABELS: Record<string, string> = {
  concept: 'Concept',
  define: 'Define',
  plan: 'Plan',
  develop: 'Develop',
  launch: 'Launch',
  sustain: 'Sustain',
};

const STATUS_LABELS: Record<string, string> = {
  not_started: 'Not Started',
  in_progress: 'In Progress',
  pending_approval: 'Pending Approval',
  approved: 'Approved',
  skipped: 'Skipped',
};

export function PhaseDetailPanel({
  phase,
  canStart,
  onStart,
  onSubmitForApproval,
  onApprove,
  onOverride,
}: PhaseDetailPanelProps) {
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [approverName, setApproverName] = useState('');
  const [approvalNotes, setApprovalNotes] = useState('');
  const [overrideName, setOverrideName] = useState('');
  const [overrideReason, setOverrideReason] = useState('');

  const progress = phase.task_count > 0
    ? Math.round((phase.completed_task_count / phase.task_count) * 100)
    : 0;

  const handleApprove = () => {
    if (approverName.trim()) {
      onApprove(approverName, approvalNotes || undefined);
      setShowApprovalModal(false);
      setApproverName('');
      setApprovalNotes('');
    }
  };

  const handleOverride = () => {
    if (overrideName.trim() && overrideReason.trim()) {
      onOverride(overrideName, overrideReason);
      setShowOverrideModal(false);
      setOverrideName('');
      setOverrideReason('');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            {PHASE_LABELS[phase.phase]} Phase
          </h2>
          <span className={`
            inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-2
            ${phase.status === 'approved' ? 'bg-green-100 text-green-800' :
              phase.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
              phase.status === 'pending_approval' ? 'bg-yellow-100 text-yellow-800' :
              'bg-gray-100 text-gray-800'}
          `}>
            {STATUS_LABELS[phase.status]}
          </span>
        </div>

        <div className="flex gap-2">
          {phase.status === 'not_started' && canStart && (
            <button
              onClick={onStart}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
            >
              <Play className="w-4 h-4 mr-1" />
              Start Phase
            </button>
          )}

          {phase.status === 'not_started' && !canStart && (
            <button
              onClick={() => setShowOverrideModal(true)}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-orange-600 border border-orange-600 hover:bg-orange-50 rounded-md"
            >
              <FastForward className="w-4 h-4 mr-1" />
              Override Sequence
            </button>
          )}

          {phase.status === 'in_progress' && (
            <button
              onClick={onSubmitForApproval}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-yellow-600 hover:bg-yellow-700 rounded-md"
            >
              <Send className="w-4 h-4 mr-1" />
              Submit for Approval
            </button>
          )}

          {phase.status === 'pending_approval' && (
            <button
              onClick={() => setShowApprovalModal(true)}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md"
            >
              <CheckCircle className="w-4 h-4 mr-1" />
              Approve Phase Exit
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-sm text-gray-500">Progress</label>
          <div className="mt-1">
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-700">{progress}%</span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              {phase.completed_task_count} of {phase.task_count} tasks completed
            </p>
          </div>
        </div>

        <div>
          <label className="text-sm text-gray-500">Timeline</label>
          <div className="mt-1 text-sm text-gray-700 space-y-1">
            {phase.target_start_date && (
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-400" />
                <span>Target: {new Date(phase.target_start_date).toLocaleDateString()} - {phase.target_end_date ? new Date(phase.target_end_date).toLocaleDateString() : 'TBD'}</span>
              </div>
            )}
            {phase.actual_start_date && (
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-green-500" />
                <span>Actual Start: {new Date(phase.actual_start_date).toLocaleDateString()}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {phase.sequence_overridden && (
        <div className="bg-orange-50 border border-orange-200 rounded-md p-3 mb-4">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-500 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-orange-800">Sequence Overridden</p>
              <p className="text-sm text-orange-700 mt-1">
                By {phase.overridden_by}: {phase.override_reason}
              </p>
            </div>
          </div>
        </div>
      )}

      {phase.approved_by && (
        <div className="bg-green-50 border border-green-200 rounded-md p-3">
          <div className="flex items-start gap-2">
            <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-green-800">
                Approved by {phase.approved_by}
              </p>
              {phase.approved_at && (
                <p className="text-sm text-green-700 mt-1">
                  on {new Date(phase.approved_at).toLocaleDateString()}
                </p>
              )}
              {phase.approval_notes && (
                <p className="text-sm text-green-700 mt-1">{phase.approval_notes}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Approval Modal */}
      {showApprovalModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Approve Phase Exit</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Approver Name *
                </label>
                <input
                  type="text"
                  value={approverName}
                  onChange={(e) => setApproverName(e.target.value)}
                  className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Enter your name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  value={approvalNotes}
                  onChange={(e) => setApprovalNotes(e.target.value)}
                  rows={3}
                  className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Any notes about this approval"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowApprovalModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={!approverName.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Approve
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Override Modal */}
      {showOverrideModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Override Phase Sequence</h3>

            <div className="bg-orange-50 border border-orange-200 rounded-md p-3 mb-4">
              <p className="text-sm text-orange-800">
                This will start the phase without waiting for the previous phase to be approved.
                Use this only when necessary.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Your Name *
                </label>
                <input
                  type="text"
                  value={overrideName}
                  onChange={(e) => setOverrideName(e.target.value)}
                  className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Enter your name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reason for Override *
                </label>
                <textarea
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  rows={3}
                  className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Explain why this override is necessary"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowOverrideModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={handleOverride}
                disabled={!overrideName.trim() || !overrideReason.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-orange-600 hover:bg-orange-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Override & Start
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
