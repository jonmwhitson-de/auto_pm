import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Lightbulb, Plus, Check, X, Clock, AlertTriangle,
  ChevronDown, ChevronRight, Loader2, Trash2
} from 'lucide-react';
import {
  getDecisions, createDecision, updateDecision, deleteDecision
} from '../../api/client';
import clsx from 'clsx';

interface DecisionsPanelProps {
  projectId: number;
}

const statusColors: Record<string, string> = {
  proposed: 'bg-yellow-100 text-yellow-700',
  accepted: 'bg-green-100 text-green-700',
  superseded: 'bg-gray-100 text-gray-600',
  deprecated: 'bg-red-100 text-red-700',
};

const statusIcons: Record<string, React.ReactNode> = {
  proposed: <Clock className="w-3 h-3" />,
  accepted: <Check className="w-3 h-3" />,
  superseded: <AlertTriangle className="w-3 h-3" />,
  deprecated: <X className="w-3 h-3" />,
};

export default function DecisionsPanel({ projectId }: DecisionsPanelProps) {
  const queryClient = useQueryClient();
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);

  const { data: decisions, isLoading } = useQuery({
    queryKey: ['decisions', projectId],
    queryFn: () => getDecisions(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (data: Parameters<typeof createDecision>[1]) =>
      createDecision(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decisions', projectId] });
      setShowForm(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof updateDecision>[1] }) =>
      updateDecision(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decisions', projectId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDecision,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decisions', projectId] });
    },
  });

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
          <Lightbulb className="w-5 h-5 text-amber-500" />
          <h3 className="font-semibold text-gray-900">Decisions (ADRs)</h3>
          <span className="text-sm text-gray-500">({decisions?.length || 0})</span>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800"
        >
          <Plus className="w-4 h-4" />
          Add Decision
        </button>
      </div>

      {showForm && (
        <DecisionForm
          onSubmit={(data) => createMutation.mutate(data)}
          onCancel={() => setShowForm(false)}
          isLoading={createMutation.isPending}
        />
      )}

      <div className="divide-y divide-gray-100">
        {decisions?.map((decision) => (
          <div key={decision.id} className="p-4">
            <div
              className="flex items-start gap-3 cursor-pointer"
              onClick={() => setExpandedId(expandedId === decision.id ? null : decision.id)}
            >
              {expandedId === decision.id ? (
                <ChevronDown className="w-5 h-5 text-gray-400 mt-0.5" />
              ) : (
                <ChevronRight className="w-5 h-5 text-gray-400 mt-0.5" />
              )}
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-medium text-gray-900">{decision.title}</h4>
                  <span className={clsx(
                    'flex items-center gap-1 text-xs px-2 py-0.5 rounded-full',
                    statusColors[decision.status]
                  )}>
                    {statusIcons[decision.status]}
                    {decision.status}
                  </span>
                  {decision.extracted_from && (
                    <span className="text-xs text-gray-400">
                      from {decision.extracted_from}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">{decision.decision}</p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm('Delete this decision?')) {
                    deleteMutation.mutate(decision.id);
                  }
                }}
                className="text-gray-400 hover:text-red-600"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            {expandedId === decision.id && (
              <div className="mt-4 ml-8 space-y-3 text-sm">
                {decision.context && (
                  <div>
                    <span className="font-medium text-gray-700">Context:</span>
                    <p className="text-gray-600 mt-1">{decision.context}</p>
                  </div>
                )}
                {decision.rationale && (
                  <div>
                    <span className="font-medium text-gray-700">Rationale:</span>
                    <p className="text-gray-600 mt-1">{decision.rationale}</p>
                  </div>
                )}
                {decision.alternatives && (
                  <div>
                    <span className="font-medium text-gray-700">Alternatives Considered:</span>
                    <ul className="list-disc list-inside text-gray-600 mt-1">
                      {JSON.parse(decision.alternatives).map((alt: string, i: number) => (
                        <li key={i}>{alt}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {decision.consequences && (
                  <div>
                    <span className="font-medium text-gray-700">Consequences:</span>
                    <p className="text-gray-600 mt-1">{decision.consequences}</p>
                  </div>
                )}

                {decision.status === 'proposed' && (
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => updateMutation.mutate({
                        id: decision.id,
                        data: { status: 'accepted' }
                      })}
                      className="flex items-center gap-1 text-sm text-green-600 hover:text-green-800"
                    >
                      <Check className="w-4 h-4" />
                      Accept
                    </button>
                    <button
                      onClick={() => updateMutation.mutate({
                        id: decision.id,
                        data: { status: 'deprecated' }
                      })}
                      className="flex items-center gap-1 text-sm text-red-600 hover:text-red-800"
                    >
                      <X className="w-4 h-4" />
                      Reject
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {(!decisions || decisions.length === 0) && !showForm && (
          <div className="p-8 text-center text-gray-500">
            <Lightbulb className="w-8 h-8 mx-auto text-gray-300 mb-2" />
            <p>No decisions recorded yet.</p>
            <p className="text-sm">Document architectural decisions and trade-offs.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function DecisionForm({
  onSubmit,
  onCancel,
  isLoading
}: {
  onSubmit: (data: Parameters<typeof createDecision>[1]) => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  const [title, setTitle] = useState('');
  const [decision, setDecision] = useState('');
  const [context, setContext] = useState('');
  const [rationale, setRationale] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !decision.trim()) return;
    onSubmit({
      title,
      decision,
      context: context || undefined,
      rationale: rationale || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-b border-gray-200 bg-gray-50">
      <div className="space-y-3">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Decision title"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          required
        />
        <textarea
          value={decision}
          onChange={(e) => setDecision(e.target.value)}
          placeholder="What was decided?"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm h-20"
          required
        />
        <textarea
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="Context (optional)"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm h-16"
        />
        <textarea
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
          placeholder="Why this decision? (optional)"
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
          Add Decision
        </button>
      </div>
    </form>
  );
}
