import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  HelpCircle, Plus, Check, X, AlertTriangle,
  ChevronDown, ChevronRight, Loader2, Trash2, Clock
} from 'lucide-react';
import {
  getAssumptions, createAssumption, updateAssumption, deleteAssumption
} from '../../api/client';
import clsx from 'clsx';

interface AssumptionsPanelProps {
  projectId: number;
}

const statusColors: Record<string, string> = {
  unvalidated: 'bg-gray-100 text-gray-700',
  validating: 'bg-blue-100 text-blue-700',
  validated: 'bg-green-100 text-green-700',
  invalidated: 'bg-red-100 text-red-700',
};

const riskColors: Record<string, string> = {
  low: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

const statusIcons: Record<string, React.ReactNode> = {
  unvalidated: <HelpCircle className="w-3 h-3" />,
  validating: <Clock className="w-3 h-3" />,
  validated: <Check className="w-3 h-3" />,
  invalidated: <X className="w-3 h-3" />,
};

export default function AssumptionsPanel({ projectId }: AssumptionsPanelProps) {
  const queryClient = useQueryClient();
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [filterRisk, setFilterRisk] = useState<string>('');

  const { data: assumptions, isLoading } = useQuery({
    queryKey: ['assumptions', projectId, filterRisk],
    queryFn: () => getAssumptions(projectId, undefined, filterRisk || undefined),
  });

  const createMutation = useMutation({
    mutationFn: (data: Parameters<typeof createAssumption>[1]) =>
      createAssumption(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assumptions', projectId] });
      setShowForm(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof updateAssumption>[1] }) =>
      updateAssumption(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assumptions', projectId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAssumption,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assumptions', projectId] });
    },
  });

  // Group assumptions by risk level
  const critical = assumptions?.filter(a => a.risk_level === 'critical' && a.status !== 'validated') || [];
  const high = assumptions?.filter(a => a.risk_level === 'high' && a.status !== 'validated') || [];
  const needsAttention = critical.length + high.length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-orange-500" />
          <h3 className="font-semibold text-gray-900">Assumptions</h3>
          <span className="text-sm text-gray-500">({assumptions?.length || 0})</span>
          {needsAttention > 0 && (
            <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
              {needsAttention} need validation
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="">All risks</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800"
          >
            <Plus className="w-4 h-4" />
            Add
          </button>
        </div>
      </div>

      {showForm && (
        <AssumptionForm
          onSubmit={(data) => createMutation.mutate(data)}
          onCancel={() => setShowForm(false)}
          isLoading={createMutation.isPending}
        />
      )}

      <div className="divide-y divide-gray-100">
        {assumptions?.map((assumption) => (
          <div key={assumption.id} className="p-4">
            <div
              className="flex items-start gap-3 cursor-pointer"
              onClick={() => setExpandedId(expandedId === assumption.id ? null : assumption.id)}
            >
              {expandedId === assumption.id ? (
                <ChevronDown className="w-5 h-5 text-gray-400 mt-0.5" />
              ) : (
                <ChevronRight className="w-5 h-5 text-gray-400 mt-0.5" />
              )}
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={clsx(
                    'flex items-center gap-1 text-xs px-2 py-0.5 rounded-full',
                    riskColors[assumption.risk_level]
                  )}>
                    {assumption.risk_level}
                  </span>
                  <span className={clsx(
                    'flex items-center gap-1 text-xs px-2 py-0.5 rounded-full',
                    statusColors[assumption.status]
                  )}>
                    {statusIcons[assumption.status]}
                    {assumption.status}
                  </span>
                  {assumption.extracted_from && (
                    <span className="text-xs text-gray-400">
                      from {assumption.extracted_from}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-900 mt-1">{assumption.assumption}</p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm('Delete this assumption?')) {
                    deleteMutation.mutate(assumption.id);
                  }
                }}
                className="text-gray-400 hover:text-red-600"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            {expandedId === assumption.id && (
              <div className="mt-4 ml-8 space-y-3 text-sm">
                {assumption.context && (
                  <div>
                    <span className="font-medium text-gray-700">Context:</span>
                    <p className="text-gray-600 mt-1">{assumption.context}</p>
                  </div>
                )}
                {assumption.impact_if_wrong && (
                  <div>
                    <span className="font-medium text-gray-700">Impact if Wrong:</span>
                    <p className="text-gray-600 mt-1">{assumption.impact_if_wrong}</p>
                  </div>
                )}
                {assumption.validation_method && (
                  <div>
                    <span className="font-medium text-gray-700">Validation Method:</span>
                    <p className="text-gray-600 mt-1">{assumption.validation_method}</p>
                  </div>
                )}
                {assumption.validation_owner && (
                  <div>
                    <span className="font-medium text-gray-700">Owner:</span>
                    <span className="text-gray-600 ml-2">{assumption.validation_owner}</span>
                  </div>
                )}
                {assumption.validation_result && (
                  <div>
                    <span className="font-medium text-gray-700">Result:</span>
                    <p className="text-gray-600 mt-1">{assumption.validation_result}</p>
                  </div>
                )}

                {assumption.status === 'unvalidated' && (
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => updateMutation.mutate({
                        id: assumption.id,
                        data: { status: 'validating' }
                      })}
                      className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
                    >
                      <Clock className="w-4 h-4" />
                      Start Validating
                    </button>
                  </div>
                )}

                {assumption.status === 'validating' && (
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => updateMutation.mutate({
                        id: assumption.id,
                        data: { status: 'validated' }
                      })}
                      className="flex items-center gap-1 text-sm text-green-600 hover:text-green-800"
                    >
                      <Check className="w-4 h-4" />
                      Mark Validated
                    </button>
                    <button
                      onClick={() => updateMutation.mutate({
                        id: assumption.id,
                        data: { status: 'invalidated' }
                      })}
                      className="flex items-center gap-1 text-sm text-red-600 hover:text-red-800"
                    >
                      <X className="w-4 h-4" />
                      Mark Invalid
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {(!assumptions || assumptions.length === 0) && !showForm && (
          <div className="p-8 text-center text-gray-500">
            <AlertTriangle className="w-8 h-8 mx-auto text-gray-300 mb-2" />
            <p>No assumptions tracked yet.</p>
            <p className="text-sm">Document and validate project assumptions.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function AssumptionForm({
  onSubmit,
  onCancel,
  isLoading
}: {
  onSubmit: (data: Parameters<typeof createAssumption>[1]) => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  const [assumption, setAssumption] = useState('');
  const [context, setContext] = useState('');
  const [impactIfWrong, setImpactIfWrong] = useState('');
  const [riskLevel, setRiskLevel] = useState('medium');
  const [validationMethod, setValidationMethod] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!assumption.trim()) return;
    onSubmit({
      assumption,
      context: context || undefined,
      impact_if_wrong: impactIfWrong || undefined,
      risk_level: riskLevel,
      validation_method: validationMethod || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-b border-gray-200 bg-gray-50">
      <div className="space-y-3">
        <textarea
          value={assumption}
          onChange={(e) => setAssumption(e.target.value)}
          placeholder="What is the assumption?"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm h-20"
          required
        />
        <div className="grid grid-cols-2 gap-3">
          <select
            value={riskLevel}
            onChange={(e) => setRiskLevel(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value="low">Low Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="high">High Risk</option>
            <option value="critical">Critical Risk</option>
          </select>
          <input
            type="text"
            value={validationMethod}
            onChange={(e) => setValidationMethod(e.target.value)}
            placeholder="How to validate?"
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>
        <textarea
          value={impactIfWrong}
          onChange={(e) => setImpactIfWrong(e.target.value)}
          placeholder="What happens if this assumption is wrong?"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm h-16"
        />
        <textarea
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="Context (optional)"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm h-16"
        />
      </div>
      <div className="flex justify-end gap-2 mt-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center gap-1 px-3 py-1.5 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 disabled:opacity-50"
        >
          {isLoading && <Loader2 className="w-3 h-3 animate-spin" />}
          Add Assumption
        </button>
      </div>
    </form>
  );
}
