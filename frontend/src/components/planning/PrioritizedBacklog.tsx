import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BarChart3, Sparkles, Loader2, Settings
} from 'lucide-react';
import {
  getPrioritizedBacklog, generateStoryEstimate, setRICEScores, setWSJFScores
} from '../../api/client';
import clsx from 'clsx';

interface PrioritizedBacklogProps {
  projectId: number;
}

export default function PrioritizedBacklog({ projectId }: PrioritizedBacklogProps) {
  const queryClient = useQueryClient();
  const [model, setModel] = useState<'rice' | 'wsjf'>('rice');
  const [editingStory, setEditingStory] = useState<number | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['prioritized-backlog', projectId, model],
    queryFn: () => getPrioritizedBacklog(projectId, model),
  });

  const generateEstimateMutation = useMutation({
    mutationFn: generateStoryEstimate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prioritized-backlog', projectId] });
    },
  });

  const setRICEMutation = useMutation({
    mutationFn: ({ storyId, scores }: { storyId: number; scores: Parameters<typeof setRICEScores>[1] }) =>
      setRICEScores(storyId, scores),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prioritized-backlog', projectId] });
      setEditingStory(null);
    },
  });

  const setWSJFMutation = useMutation({
    mutationFn: ({ storyId, scores }: { storyId: number; scores: Parameters<typeof setWSJFScores>[1] }) =>
      setWSJFScores(storyId, scores),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prioritized-backlog', projectId] });
      setEditingStory(null);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
      </div>
    );
  }

  const stories = data?.stories || [];
  const scoredCount = stories.filter(s => s.priority_score !== null).length;

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-indigo-500" />
          <h3 className="font-semibold text-gray-900">Prioritized Backlog</h3>
          <span className="text-sm text-gray-500">
            ({scoredCount}/{stories.length} scored)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-gray-300 overflow-hidden">
            <button
              onClick={() => setModel('rice')}
              className={clsx(
                'px-3 py-1.5 text-sm font-medium',
                model === 'rice'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              )}
            >
              RICE
            </button>
            <button
              onClick={() => setModel('wsjf')}
              className={clsx(
                'px-3 py-1.5 text-sm font-medium border-l border-gray-300',
                model === 'wsjf'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              )}
            >
              WSJF
            </button>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">Rank</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">Story</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">Epic</th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 uppercase">Points</th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 uppercase">Est (h)</th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                {model === 'rice' ? 'RICE Score' : 'WSJF Score'}
              </th>
              <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {stories.map((story, index) => (
              <tr key={story.id} className="hover:bg-gray-50">
                <td className="py-3 px-4">
                  <span className={clsx(
                    'inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium',
                    index === 0 ? 'bg-yellow-100 text-yellow-800' :
                    index === 1 ? 'bg-gray-200 text-gray-700' :
                    index === 2 ? 'bg-amber-100 text-amber-800' :
                    'bg-gray-100 text-gray-600'
                  )}>
                    {index + 1}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className="font-medium text-gray-900">{story.title}</span>
                </td>
                <td className="py-3 px-4 text-sm text-gray-600">{story.epic_title}</td>
                <td className="py-3 px-4 text-right text-sm text-gray-600">
                  {story.story_points || '-'}
                </td>
                <td className="py-3 px-4 text-right text-sm text-gray-600">
                  {story.estimate_p50 || story.estimated_hours || '-'}
                </td>
                <td className="py-3 px-4 text-right">
                  {story.priority_score !== null ? (
                    <span className="font-semibold text-indigo-600">
                      {story.priority_score.toFixed(1)}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="py-3 px-4 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <button
                      onClick={() => generateEstimateMutation.mutate(story.id)}
                      disabled={generateEstimateMutation.isPending}
                      className="text-purple-600 hover:text-purple-800"
                      title="Generate AI estimate"
                    >
                      {generateEstimateMutation.isPending &&
                       generateEstimateMutation.variables === story.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Sparkles className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={() => setEditingStory(editingStory === story.id ? null : story.id)}
                      className="text-gray-400 hover:text-gray-600"
                      title="Edit scores"
                    >
                      <Settings className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {editingStory && (
          <div className="border-t border-gray-200 p-4 bg-gray-50">
            <h4 className="font-medium text-gray-900 mb-3">
              Set {model === 'rice' ? 'RICE' : 'WSJF'} Scores for Story #{editingStory}
            </h4>
            {model === 'rice' ? (
              <RICEForm
                onSubmit={(scores) => setRICEMutation.mutate({ storyId: editingStory, scores })}
                onCancel={() => setEditingStory(null)}
                isLoading={setRICEMutation.isPending}
              />
            ) : (
              <WSJFForm
                onSubmit={(scores) => setWSJFMutation.mutate({ storyId: editingStory, scores })}
                onCancel={() => setEditingStory(null)}
                isLoading={setWSJFMutation.isPending}
              />
            )}
          </div>
        )}

        {stories.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            <BarChart3 className="w-8 h-8 mx-auto text-gray-300 mb-2" />
            <p>No stories to prioritize yet.</p>
            <p className="text-sm">Analyze a PRD to generate stories first.</p>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-xs text-gray-500">
          {model === 'rice' ? (
            <p><strong>RICE</strong> = (Reach x Impact x Confidence) / Effort. Higher scores = higher priority.</p>
          ) : (
            <p><strong>WSJF</strong> = Cost of Delay / Job Size. Higher scores = do these first.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function RICEForm({
  onSubmit,
  onCancel,
  isLoading
}: {
  onSubmit: (scores: Parameters<typeof setRICEScores>[1]) => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  const [reach, setReach] = useState(100);
  const [impact, setImpact] = useState(1);
  const [confidence, setConfidence] = useState(0.8);
  const [effort, setEffort] = useState(1);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ reach, impact, confidence, effort });
  };

  const score = effort > 0 ? (reach * impact * confidence) / effort : 0;

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-5 gap-4 items-end">
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Reach (users/quarter)
        </label>
        <input
          type="number"
          value={reach}
          onChange={(e) => setReach(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          min="0"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Impact
        </label>
        <select
          value={impact}
          onChange={(e) => setImpact(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
        >
          <option value={3}>Massive (3x)</option>
          <option value={2}>High (2x)</option>
          <option value={1}>Medium (1x)</option>
          <option value={0.5}>Low (0.5x)</option>
          <option value={0.25}>Minimal (0.25x)</option>
        </select>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Confidence
        </label>
        <select
          value={confidence}
          onChange={(e) => setConfidence(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
        >
          <option value={1}>High (100%)</option>
          <option value={0.8}>Medium (80%)</option>
          <option value={0.5}>Low (50%)</option>
        </select>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Effort (person-months)
        </label>
        <input
          type="number"
          value={effort}
          onChange={(e) => setEffort(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          min="0.1"
          step="0.1"
        />
      </div>
      <div className="flex items-center gap-2">
        <div className="text-lg font-bold text-indigo-600">{score.toFixed(1)}</div>
        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center gap-1 px-3 py-2 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 disabled:opacity-50"
        >
          {isLoading && <Loader2 className="w-3 h-3 animate-spin" />}
          Save
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

function WSJFForm({
  onSubmit,
  onCancel,
  isLoading
}: {
  onSubmit: (scores: Parameters<typeof setWSJFScores>[1]) => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  const [businessValue, setBusinessValue] = useState(8);
  const [timeCriticality, setTimeCriticality] = useState(5);
  const [riskReduction, setRiskReduction] = useState(5);
  const [jobSize, setJobSize] = useState(5);

  const fibonacci = [1, 2, 3, 5, 8, 13, 21];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      business_value: businessValue,
      time_criticality: timeCriticality,
      risk_reduction: riskReduction,
      job_size: jobSize
    });
  };

  const costOfDelay = businessValue + timeCriticality + riskReduction;
  const score = jobSize > 0 ? costOfDelay / jobSize : 0;

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-5 gap-4 items-end">
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Business Value
        </label>
        <select
          value={businessValue}
          onChange={(e) => setBusinessValue(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
        >
          {fibonacci.map(n => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Time Criticality
        </label>
        <select
          value={timeCriticality}
          onChange={(e) => setTimeCriticality(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
        >
          {fibonacci.map(n => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Risk Reduction / OE
        </label>
        <select
          value={riskReduction}
          onChange={(e) => setRiskReduction(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
        >
          {fibonacci.map(n => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Job Size
        </label>
        <select
          value={jobSize}
          onChange={(e) => setJobSize(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
        >
          {fibonacci.map(n => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <div className="text-lg font-bold text-indigo-600">{score.toFixed(1)}</div>
        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center gap-1 px-3 py-2 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 disabled:opacity-50"
        >
          {isLoading && <Loader2 className="w-3 h-3 animate-spin" />}
          Save
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
