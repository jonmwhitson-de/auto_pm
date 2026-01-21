import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  GitBranch, Plus, Sparkles, Loader2, Trash2, ArrowRight,
  AlertCircle, CheckCircle, Clock, XCircle
} from 'lucide-react';
import {
  getDependencies, createDependency, updateDependency, deleteDependency,
  inferDependencies, getCriticalPath
} from '../../api/client';
import clsx from 'clsx';

interface DependencyMapProps {
  projectId: number;
  stories: Array<{ id: number; title: string; epic_id: number }>;
  epics: Array<{ id: number; title: string }>;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  in_progress: 'bg-blue-100 text-blue-700',
  resolved: 'bg-green-100 text-green-700',
  blocked: 'bg-red-100 text-red-700',
};

const statusIcons: Record<string, React.ReactNode> = {
  pending: <Clock className="w-3 h-3" />,
  in_progress: <AlertCircle className="w-3 h-3" />,
  resolved: <CheckCircle className="w-3 h-3" />,
  blocked: <XCircle className="w-3 h-3" />,
};

const depTypeLabels: Record<string, string> = {
  depends_on: 'depends on',
  blocks: 'blocks',
  related: 'related to',
};

export default function DependencyMap({ projectId, stories, epics }: DependencyMapProps) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data: dependencies, isLoading } = useQuery({
    queryKey: ['dependencies', projectId, statusFilter],
    queryFn: () => getDependencies(projectId, statusFilter || undefined),
  });

  const { data: criticalPath } = useQuery({
    queryKey: ['critical-path', projectId],
    queryFn: () => getCriticalPath(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (data: Parameters<typeof createDependency>[1]) =>
      createDependency(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dependencies', projectId] });
      queryClient.invalidateQueries({ queryKey: ['critical-path', projectId] });
      setShowForm(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof updateDependency>[1] }) =>
      updateDependency(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dependencies', projectId] });
      queryClient.invalidateQueries({ queryKey: ['critical-path', projectId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDependency,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dependencies', projectId] });
      queryClient.invalidateQueries({ queryKey: ['critical-path', projectId] });
    },
  });

  const inferMutation = useMutation({
    mutationFn: () => inferDependencies(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dependencies', projectId] });
      queryClient.invalidateQueries({ queryKey: ['critical-path', projectId] });
    },
  });

  const getItemName = (type: string, id: number): string => {
    if (type === 'story') {
      const story = stories.find(s => s.id === id);
      return story?.title || `Story #${id}`;
    }
    if (type === 'epic') {
      const epic = epics.find(e => e.id === id);
      return epic?.title || `Epic #${id}`;
    }
    return `Task #${id}`;
  };

  // Count by status
  const pendingCount = dependencies?.filter(d => d.status === 'pending').length || 0;
  const blockedCount = dependencies?.filter(d => d.status === 'blocked').length || 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Critical Path Summary */}
      {criticalPath && criticalPath.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <GitBranch className="w-5 h-5 text-amber-600" />
            <h4 className="font-semibold text-amber-800">Critical Path</h4>
            <span className="text-sm text-amber-600">
              Total: {criticalPath[criticalPath.length - 1]?.total_duration || 0}h
            </span>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {criticalPath.map((item, i) => (
              <div key={i} className="flex items-center gap-1">
                <span className="text-sm bg-amber-100 px-2 py-1 rounded">
                  {item.item.split(':')[1] ? getItemName(item.item.split(':')[0], parseInt(item.item.split(':')[1])) : item.item}
                </span>
                {i < criticalPath.length - 1 && (
                  <ArrowRight className="w-4 h-4 text-amber-400" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dependencies List */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-indigo-500" />
            <h3 className="font-semibold text-gray-900">Dependencies</h3>
            <span className="text-sm text-gray-500">({dependencies?.length || 0})</span>
            {pendingCount > 0 && (
              <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full">
                {pendingCount} pending
              </span>
            )}
            {blockedCount > 0 && (
              <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                {blockedCount} blocked
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="blocked">Blocked</option>
            </select>
            <button
              onClick={() => inferMutation.mutate()}
              disabled={inferMutation.isPending}
              className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-800"
            >
              {inferMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              Auto-detect
            </button>
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
          <DependencyForm
            stories={stories}
            epics={epics}
            onSubmit={(data) => createMutation.mutate(data)}
            onCancel={() => setShowForm(false)}
            isLoading={createMutation.isPending}
          />
        )}

        <div className="divide-y divide-gray-100">
          {dependencies?.map((dep) => (
            <div key={dep.id} className="p-4 flex items-start gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-gray-900">
                    {getItemName(dep.source_type, dep.source_id)}
                  </span>
                  <span className="text-gray-500 text-sm">
                    {depTypeLabels[dep.dependency_type]}
                  </span>
                  <ArrowRight className="w-4 h-4 text-gray-400" />
                  <span className="font-medium text-gray-900">
                    {getItemName(dep.target_type, dep.target_id)}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <span className={clsx(
                    'flex items-center gap-1 text-xs px-2 py-0.5 rounded-full',
                    statusColors[dep.status]
                  )}>
                    {statusIcons[dep.status]}
                    {dep.status.replace('_', ' ')}
                  </span>
                  {dep.inferred && (
                    <span className="flex items-center gap-1 text-xs text-purple-600">
                      <Sparkles className="w-3 h-3" />
                      AI-detected
                      {dep.confidence && ` (${Math.round(dep.confidence * 100)}%)`}
                    </span>
                  )}
                </div>
                {dep.inference_reason && (
                  <p className="text-xs text-gray-500 mt-1">{dep.inference_reason}</p>
                )}
                {dep.notes && (
                  <p className="text-sm text-gray-600 mt-1">{dep.notes}</p>
                )}
              </div>

              <div className="flex items-center gap-2">
                {dep.status === 'pending' && (
                  <button
                    onClick={() => updateMutation.mutate({
                      id: dep.id,
                      data: { status: 'in_progress' }
                    })}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Start
                  </button>
                )}
                {dep.status === 'in_progress' && (
                  <button
                    onClick={() => updateMutation.mutate({
                      id: dep.id,
                      data: { status: 'resolved' }
                    })}
                    className="text-xs text-green-600 hover:text-green-800"
                  >
                    Resolve
                  </button>
                )}
                <button
                  onClick={() => {
                    if (confirm('Delete this dependency?')) {
                      deleteMutation.mutate(dep.id);
                    }
                  }}
                  className="text-gray-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}

          {(!dependencies || dependencies.length === 0) && !showForm && (
            <div className="p-8 text-center text-gray-500">
              <GitBranch className="w-8 h-8 mx-auto text-gray-300 mb-2" />
              <p>No dependencies mapped yet.</p>
              <p className="text-sm">Add dependencies manually or use AI to auto-detect them.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DependencyForm({
  stories,
  epics,
  onSubmit,
  onCancel,
  isLoading
}: {
  stories: Array<{ id: number; title: string; epic_id: number }>;
  epics: Array<{ id: number; title: string }>;
  onSubmit: (data: Parameters<typeof createDependency>[1]) => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  const [sourceType, setSourceType] = useState('story');
  const [sourceId, setSourceId] = useState<number | ''>('');
  const [targetType, setTargetType] = useState('story');
  const [targetId, setTargetId] = useState<number | ''>('');
  const [depType, setDepType] = useState('depends_on');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceId || !targetId) return;
    onSubmit({
      source_type: sourceType,
      source_id: Number(sourceId),
      target_type: targetType,
      target_id: Number(targetId),
      dependency_type: depType,
      notes: notes || undefined,
    });
  };

  const getOptions = (type: string) => {
    if (type === 'story') return stories;
    if (type === 'epic') return epics;
    return [];
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-b border-gray-200 bg-gray-50">
      <div className="grid grid-cols-7 gap-3 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Type</label>
          <select
            value={sourceType}
            onChange={(e) => { setSourceType(e.target.value); setSourceId(''); }}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
          >
            <option value="story">Story</option>
            <option value="epic">Epic</option>
          </select>
        </div>
        <div className="col-span-2">
          <label className="block text-xs font-medium text-gray-700 mb-1">Source</label>
          <select
            value={sourceId}
            onChange={(e) => setSourceId(Number(e.target.value))}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
            required
          >
            <option value="">Select...</option>
            {getOptions(sourceType).map((item) => (
              <option key={item.id} value={item.id}>{item.title}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Relation</label>
          <select
            value={depType}
            onChange={(e) => setDepType(e.target.value)}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
          >
            <option value="depends_on">depends on</option>
            <option value="blocks">blocks</option>
            <option value="related">related to</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Type</label>
          <select
            value={targetType}
            onChange={(e) => { setTargetType(e.target.value); setTargetId(''); }}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
          >
            <option value="story">Story</option>
            <option value="epic">Epic</option>
          </select>
        </div>
        <div className="col-span-2">
          <label className="block text-xs font-medium text-gray-700 mb-1">Target</label>
          <select
            value={targetId}
            onChange={(e) => setTargetId(Number(e.target.value))}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
            required
          >
            <option value="">Select...</option>
            {getOptions(targetType).map((item) => (
              <option key={item.id} value={item.id}>{item.title}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="mt-3">
        <input
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Notes (optional)"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
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
          Add Dependency
        </button>
      </div>
    </form>
  );
}
