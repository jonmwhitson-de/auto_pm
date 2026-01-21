import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Loader2, Play, ChevronDown, ChevronRight,
  Calendar, Target, Clock, Hash, GitBranch, Workflow
} from 'lucide-react';
import { getProject, analyzeProject, getSprints, createSprint, planSprint } from '../api/client';
import type { Epic, Story, Sprint } from '../types';
import clsx from 'clsx';
import DecisionsPanel from '../components/planning/DecisionsPanel';
import AssumptionsPanel from '../components/planning/AssumptionsPanel';
import DependencyMap from '../components/planning/DependencyMap';
import PrioritizedBacklog from '../components/planning/PrioritizedBacklog';

const priorityColors = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

const statusColors = {
  backlog: 'bg-gray-100 text-gray-700',
  ready: 'bg-yellow-100 text-yellow-700',
  in_progress: 'bg-blue-100 text-blue-700',
  in_review: 'bg-purple-100 text-purple-700',
  done: 'bg-green-100 text-green-700',
};

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [expandedEpics, setExpandedEpics] = useState<Set<number>>(new Set());
  const [selectedStories, setSelectedStories] = useState<Set<number>>(new Set());
  const [activeTab, setActiveTab] = useState<'backlog' | 'sprints' | 'planning'>('backlog');

  const projectQuery = useQuery({
    queryKey: ['project', id],
    queryFn: () => getProject(Number(id)),
  });

  const sprintsQuery = useQuery({
    queryKey: ['sprints', id],
    queryFn: () => getSprints(Number(id)),
    enabled: !!id,
  });

  const analyzeMutation = useMutation({
    mutationFn: () => analyzeProject(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] });
    },
  });

  const createSprintMutation = useMutation({
    mutationFn: createSprint,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sprints', id] });
    },
  });

  const planSprintMutation = useMutation({
    mutationFn: ({ sprintId, storyIds }: { sprintId: number; storyIds: number[] }) =>
      planSprint(sprintId, storyIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] });
      queryClient.invalidateQueries({ queryKey: ['sprints', id] });
      setSelectedStories(new Set());
    },
  });

  if (projectQuery.isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  const project = projectQuery.data;
  if (!project) return <div>Project not found</div>;

  const toggleEpic = (epicId: number) => {
    const next = new Set(expandedEpics);
    if (next.has(epicId)) {
      next.delete(epicId);
    } else {
      next.add(epicId);
    }
    setExpandedEpics(next);
  };

  const toggleStory = (storyId: number) => {
    const next = new Set(selectedStories);
    if (next.has(storyId)) {
      next.delete(storyId);
    } else {
      next.add(storyId);
    }
    setSelectedStories(next);
  };

  const handleCreateSprint = () => {
    const sprintNumber = (sprintsQuery.data?.length || 0) + 1;
    createSprintMutation.mutate({
      project_id: Number(id),
      name: `Sprint ${sprintNumber}`,
    });
  };

  const handleAssignToSprint = (sprintId: number) => {
    if (selectedStories.size === 0) return;
    planSprintMutation.mutate({
      sprintId,
      storyIds: Array.from(selectedStories),
    });
  };

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          {project.description && (
            <p className="text-gray-600 mt-1">{project.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Link
            to={`/projects/${id}/lifecycle`}
            className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-purple-700 transition"
          >
            <Workflow className="w-4 h-4" />
            Offer Lifecycle
          </Link>
          {project.status === 'draft' && (
            <button
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending}
              className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition disabled:opacity-50"
            >
              {analyzeMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              Analyze PRD
            </button>
          )}
        </div>
      </div>

      {project.status === 'draft' && !project.epics?.length && (
        <div className="bg-gray-50 rounded-lg p-8 text-center border-2 border-dashed border-gray-300">
          <Target className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to analyze</h3>
          <p className="text-gray-600 mb-4">
            Click "Analyze PRD" to generate epics, stories, and tasks from your requirements
          </p>
        </div>
      )}

      {(project.epics?.length ?? 0) > 0 && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <Hash className="w-4 h-4" />
                <span className="text-sm">Story Points</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{project.total_story_points || 0}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <Clock className="w-4 h-4" />
                <span className="text-sm">Estimated Hours</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{project.total_estimated_hours || 0}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <Target className="w-4 h-4" />
                <span className="text-sm">Epics</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{project.epics?.length || 0}</p>
            </div>
          </div>

          <div className="flex gap-4 mb-4 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('backlog')}
              className={clsx(
                'px-4 py-2 font-medium border-b-2 -mb-px transition',
                activeTab === 'backlog'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              )}
            >
              Backlog
            </button>
            <button
              onClick={() => setActiveTab('sprints')}
              className={clsx(
                'px-4 py-2 font-medium border-b-2 -mb-px transition',
                activeTab === 'sprints'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              )}
            >
              Sprints
            </button>
            <button
              onClick={() => setActiveTab('planning')}
              className={clsx(
                'px-4 py-2 font-medium border-b-2 -mb-px transition flex items-center gap-2',
                activeTab === 'planning'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              )}
            >
              <GitBranch className="w-4 h-4" />
              Planning
            </button>
          </div>

          {activeTab === 'backlog' && (
            <div className="space-y-4">
              {selectedStories.size > 0 && (
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 flex items-center justify-between">
                  <span className="text-indigo-700 font-medium">
                    {selectedStories.size} stories selected
                  </span>
                  <div className="flex gap-2">
                    {sprintsQuery.data?.map(sprint => (
                      <button
                        key={sprint.id}
                        onClick={() => handleAssignToSprint(sprint.id)}
                        className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700"
                      >
                        Add to {sprint.name}
                      </button>
                    ))}
                    <button
                      onClick={handleCreateSprint}
                      className="bg-white text-indigo-600 border border-indigo-600 px-3 py-1 rounded text-sm hover:bg-indigo-50"
                    >
                      New Sprint
                    </button>
                  </div>
                </div>
              )}

              {project.epics?.map((epic: Epic) => (
                <div key={epic.id} className="bg-white rounded-lg border border-gray-200">
                  <button
                    onClick={() => toggleEpic(epic.id)}
                    className="w-full flex items-center gap-3 p-4 text-left hover:bg-gray-50"
                  >
                    {expandedEpics.has(epic.id) ? (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{epic.title}</h3>
                      {epic.description && (
                        <p className="text-sm text-gray-600 mt-1">{epic.description}</p>
                      )}
                    </div>
                    <span className={clsx('text-xs px-2 py-1 rounded', priorityColors[epic.priority])}>
                      {epic.priority}
                    </span>
                  </button>

                  {expandedEpics.has(epic.id) && epic.stories && (
                    <div className="border-t border-gray-200">
                      {epic.stories.map((story: Story) => (
                        <div
                          key={story.id}
                          className={clsx(
                            'flex items-start gap-3 p-4 border-b border-gray-100 last:border-b-0',
                            story.sprint_id && 'bg-gray-50'
                          )}
                        >
                          {!story.sprint_id && (
                            <input
                              type="checkbox"
                              checked={selectedStories.has(story.id)}
                              onChange={() => toggleStory(story.id)}
                              className="mt-1 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                            />
                          )}
                          <div className="flex-1 ml-2">
                            <div className="flex items-center gap-2">
                              <h4 className="font-medium text-gray-900">{story.title}</h4>
                              <span className={clsx('text-xs px-2 py-0.5 rounded', statusColors[story.status])}>
                                {story.status.replace('_', ' ')}
                              </span>
                            </div>
                            {story.description && (
                              <p className="text-sm text-gray-600 mt-1">{story.description}</p>
                            )}
                            <div className="flex gap-4 mt-2 text-xs text-gray-500">
                              {story.story_points && (
                                <span className="flex items-center gap-1">
                                  <Hash className="w-3 h-3" />
                                  {story.story_points} pts
                                </span>
                              )}
                              {story.estimated_hours && (
                                <span className="flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  {story.estimated_hours}h
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {activeTab === 'sprints' && (
            <div className="space-y-4">
              <button
                onClick={handleCreateSprint}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700"
              >
                Create Sprint
              </button>

              {sprintsQuery.data?.map((sprint: Sprint) => (
                <div key={sprint.id} className="bg-white rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-gray-900">{sprint.name}</h3>
                      {sprint.goal && (
                        <p className="text-sm text-gray-600">{sprint.goal}</p>
                      )}
                    </div>
                    <div className="flex gap-4 text-sm text-gray-600">
                      <span>{sprint.total_points || 0} pts</span>
                      <span>{sprint.total_hours || 0}h</span>
                    </div>
                  </div>
                  {sprint.stories.length > 0 ? (
                    <div className="space-y-2">
                      {sprint.stories.map(story => (
                        <div key={story.id} className="flex items-center justify-between bg-gray-50 rounded p-2">
                          <span className="text-sm font-medium">{story.title}</span>
                          <div className="flex gap-2 text-xs text-gray-500">
                            <span>{story.story_points} pts</span>
                            <span className={clsx('px-2 py-0.5 rounded', statusColors[story.status])}>
                              {story.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 text-center py-4">
                      No stories assigned. Select stories from the backlog to add them.
                    </p>
                  )}
                </div>
              ))}

              {(!sprintsQuery.data || sprintsQuery.data.length === 0) && (
                <div className="bg-gray-50 rounded-lg p-8 text-center border-2 border-dashed border-gray-300">
                  <Calendar className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No sprints yet</h3>
                  <p className="text-gray-600">Create a sprint and assign stories to plan your work</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'planning' && (
            <div className="space-y-6">
              {/* Prioritized Backlog */}
              <PrioritizedBacklog projectId={Number(id)} />

              {/* Dependency Map */}
              <DependencyMap
                projectId={Number(id)}
                stories={project.epics?.flatMap(e => e.stories?.map(s => ({
                  id: s.id,
                  title: s.title,
                  epic_id: e.id
                })) || []) || []}
                epics={project.epics?.map(e => ({
                  id: e.id,
                  title: e.title
                })) || []}
              />

              {/* Decisions & Assumptions */}
              <div className="grid grid-cols-2 gap-6">
                <DecisionsPanel projectId={Number(id)} />
                <AssumptionsPanel projectId={Number(id)} />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
