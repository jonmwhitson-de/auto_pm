import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Inbox, Plus, Loader2, AlertCircle,
  MessageSquare, ArrowRight, Trash2,
  Bug, Sparkles, Wrench, Shield, AlertTriangle, HelpCircle
} from 'lucide-react';
import {
  getIntakes, createIntake, processIntake, deleteIntake, getIntakeStats,
  type IntakeSummary
} from '../api/client';
import clsx from 'clsx';

const typeIcons: Record<string, React.ReactNode> = {
  bug: <Bug className="w-4 h-4" />,
  feature: <Sparkles className="w-4 h-4" />,
  tech_debt: <Wrench className="w-4 h-4" />,
  risk: <AlertTriangle className="w-4 h-4" />,
  compliance: <Shield className="w-4 h-4" />,
  enhancement: <Sparkles className="w-4 h-4" />,
  unknown: <HelpCircle className="w-4 h-4" />,
};

const typeColors: Record<string, string> = {
  bug: 'bg-red-100 text-red-700',
  feature: 'bg-blue-100 text-blue-700',
  tech_debt: 'bg-yellow-100 text-yellow-700',
  risk: 'bg-orange-100 text-orange-700',
  compliance: 'bg-purple-100 text-purple-700',
  enhancement: 'bg-green-100 text-green-700',
  unknown: 'bg-gray-100 text-gray-700',
};

const statusColors: Record<string, string> = {
  new: 'bg-blue-100 text-blue-700',
  triaging: 'bg-yellow-100 text-yellow-700',
  needs_clarification: 'bg-orange-100 text-orange-700',
  ready: 'bg-green-100 text-green-700',
  converted: 'bg-purple-100 text-purple-700',
  duplicate: 'bg-gray-100 text-gray-600',
  rejected: 'bg-red-100 text-red-700',
};

export default function IntakeInboxPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showNewIntakeForm, setShowNewIntakeForm] = useState(false);

  const { data: intakes, isLoading } = useQuery({
    queryKey: ['intakes', statusFilter],
    queryFn: () => getIntakes(statusFilter || undefined),
  });

  const { data: stats } = useQuery({
    queryKey: ['intake-stats'],
    queryFn: getIntakeStats,
  });

  const processMutation = useMutation({
    mutationFn: processIntake,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intakes'] });
      queryClient.invalidateQueries({ queryKey: ['intake-stats'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteIntake,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intakes'] });
      queryClient.invalidateQueries({ queryKey: ['intake-stats'] });
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Intake Inbox</h1>
          <p className="text-gray-600">
            {stats?.needs_attention || 0} items need attention
          </p>
        </div>
        <button
          onClick={() => setShowNewIntakeForm(true)}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700"
        >
          <Plus className="w-4 h-4" />
          New Intake
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-5 gap-4 mb-6">
          <StatCard
            label="New"
            count={stats.by_status.new || 0}
            color="blue"
            onClick={() => setStatusFilter('new')}
            active={statusFilter === 'new'}
          />
          <StatCard
            label="Needs Clarification"
            count={stats.by_status.needs_clarification || 0}
            color="orange"
            onClick={() => setStatusFilter('needs_clarification')}
            active={statusFilter === 'needs_clarification'}
          />
          <StatCard
            label="Ready"
            count={stats.by_status.ready || 0}
            color="green"
            onClick={() => setStatusFilter('ready')}
            active={statusFilter === 'ready'}
          />
          <StatCard
            label="Converted"
            count={stats.by_status.converted || 0}
            color="purple"
            onClick={() => setStatusFilter('converted')}
            active={statusFilter === 'converted'}
          />
          <StatCard
            label="All"
            count={stats.total}
            color="gray"
            onClick={() => setStatusFilter('')}
            active={statusFilter === ''}
          />
        </div>
      )}

      {/* New Intake Modal */}
      {showNewIntakeForm && (
        <NewIntakeModal
          onClose={() => setShowNewIntakeForm(false)}
          onSuccess={() => {
            setShowNewIntakeForm(false);
            queryClient.invalidateQueries({ queryKey: ['intakes'] });
            queryClient.invalidateQueries({ queryKey: ['intake-stats'] });
          }}
        />
      )}

      {/* Intake List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        </div>
      ) : !intakes?.length ? (
        <div className="text-center py-16 bg-white rounded-lg border border-gray-200">
          <Inbox className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No intakes yet</h2>
          <p className="text-gray-600 mb-6">
            Add incoming requests from Slack, email, or paste content directly
          </p>
          <button
            onClick={() => setShowNewIntakeForm(true)}
            className="inline-flex items-center gap-2 bg-indigo-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-indigo-700"
          >
            <Plus className="w-5 h-5" />
            New Intake
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {intakes.map((intake) => (
            <IntakeCard
              key={intake.id}
              intake={intake}
              onProcess={() => processMutation.mutate(intake.id)}
              onDelete={() => deleteMutation.mutate(intake.id)}
              onView={() => navigate(`/intake/${intake.id}`)}
              isProcessing={processMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function StatCard({ label, count, color, onClick, active }: {
  label: string;
  count: number;
  color: string;
  onClick: () => void;
  active: boolean;
}) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    orange: 'bg-orange-50 border-orange-200 text-orange-700',
    green: 'bg-green-50 border-green-200 text-green-700',
    purple: 'bg-purple-50 border-purple-200 text-purple-700',
    gray: 'bg-gray-50 border-gray-200 text-gray-700',
  };

  return (
    <button
      onClick={onClick}
      className={clsx(
        'p-4 rounded-lg border-2 text-left transition',
        active ? 'ring-2 ring-indigo-500' : '',
        colors[color]
      )}
    >
      <p className="text-2xl font-bold">{count}</p>
      <p className="text-sm">{label}</p>
    </button>
  );
}

function IntakeCard({ intake, onProcess, onDelete, onView, isProcessing }: {
  intake: IntakeSummary;
  onProcess: () => void;
  onDelete: () => void;
  onView: () => void;
  isProcessing: boolean;
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {intake.inferred_type && (
              <span className={clsx(
                'flex items-center gap-1 text-xs px-2 py-1 rounded-full',
                typeColors[intake.inferred_type]
              )}>
                {typeIcons[intake.inferred_type]}
                {intake.inferred_type.replace('_', ' ')}
              </span>
            )}
            <span className={clsx(
              'text-xs px-2 py-1 rounded-full',
              statusColors[intake.status]
            )}>
              {intake.status.replace('_', ' ')}
            </span>
            {intake.priority_score !== null && (
              <span className="text-xs text-gray-500">
                Priority: {Math.round(intake.priority_score)}
              </span>
            )}
          </div>

          <h3
            className="font-semibold text-gray-900 cursor-pointer hover:text-indigo-600"
            onClick={onView}
          >
            {intake.title}
          </h3>

          <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
            <span>Source: {intake.source}</span>
            <span>{new Date(intake.received_at).toLocaleDateString()}</span>
            {intake.missing_info_count > 0 && (
              <span className="flex items-center gap-1 text-orange-600">
                <AlertCircle className="w-3 h-3" />
                {intake.missing_info_count} missing fields
              </span>
            )}
            {intake.blocking_questions_count > 0 && (
              <span className="flex items-center gap-1 text-red-600">
                <MessageSquare className="w-3 h-3" />
                {intake.blocking_questions_count} blocking questions
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {intake.status === 'new' && (
            <button
              onClick={onProcess}
              disabled={isProcessing}
              className="flex items-center gap-1 text-indigo-600 hover:text-indigo-800 text-sm font-medium"
            >
              {isProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              Process
            </button>
          )}
          {intake.status === 'ready' && (
            <button
              onClick={onView}
              className="flex items-center gap-1 text-green-600 hover:text-green-800 text-sm font-medium"
            >
              <ArrowRight className="w-4 h-4" />
              Convert
            </button>
          )}
          <button
            onClick={onDelete}
            className="text-gray-400 hover:text-red-600"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function NewIntakeModal({ onClose, onSuccess }: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [source, setSource] = useState('manual');

  const createMutation = useMutation({
    mutationFn: createIntake,
    onSuccess: () => {
      onSuccess();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    createMutation.mutate({ title, raw_content: content, source });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">New Intake</h2>
          <p className="text-gray-600">Add a new request to be triaged</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Source
            </label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="manual">Manual Entry</option>
              <option value="slack">Slack</option>
              <option value="teams">Teams</option>
              <option value="email">Email</option>
              <option value="meeting_transcript">Meeting Transcript</option>
              <option value="support_ticket">Support Ticket</option>
              <option value="sales_request">Sales Request</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title / Subject
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Brief description of the request"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Content
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste the full request content here..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg h-48 font-mono text-sm"
              required
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:text-gray-900"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              {createMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Create Intake
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
