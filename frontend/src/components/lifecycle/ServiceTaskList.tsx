import { useState } from 'react';
import { CheckCircle, Circle, Clock, AlertCircle, Ban, MoreHorizontal, Plus, ChevronDown, ChevronRight } from 'lucide-react';
import type { ServiceTask, ServiceTaskStatus } from '../../types';

interface ServiceTaskListProps {
  tasks: ServiceTask[];
  onTaskStatusChange: (taskId: number, status: ServiceTaskStatus) => void;
  onTaskClick: (task: ServiceTask) => void;
  onAddTask: () => void;
}

const STATUS_CONFIG: Record<ServiceTaskStatus, { label: string; color: string; icon: typeof Circle }> = {
  not_started: { label: 'Not Started', color: 'text-gray-400', icon: Circle },
  in_progress: { label: 'In Progress', color: 'text-blue-600', icon: Clock },
  blocked: { label: 'Blocked', color: 'text-red-600', icon: AlertCircle },
  completed: { label: 'Completed', color: 'text-green-600', icon: CheckCircle },
  deferred: { label: 'Deferred', color: 'text-orange-500', icon: MoreHorizontal },
  not_applicable: { label: 'N/A', color: 'text-gray-500', icon: Ban },
};

const CATEGORY_COLORS: Record<string, string> = {
  'Legal & Compliance': 'bg-purple-100 text-purple-700',
  'Finance & Pricing': 'bg-green-100 text-green-700',
  'Marketing & Communications': 'bg-pink-100 text-pink-700',
  'Sales Enablement': 'bg-blue-100 text-blue-700',
  'Product Management': 'bg-indigo-100 text-indigo-700',
  'Engineering & Technical': 'bg-cyan-100 text-cyan-700',
  'Operations & Support': 'bg-orange-100 text-orange-700',
  'Partner & Ecosystem': 'bg-teal-100 text-teal-700',
  'Training & Documentation': 'bg-yellow-100 text-yellow-700',
  'Quality & Certification': 'bg-red-100 text-red-700',
};

export function ServiceTaskList({ tasks, onTaskStatusChange, onTaskClick, onAddTask }: ServiceTaskListProps) {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [filterStatus, setFilterStatus] = useState<ServiceTaskStatus | 'all'>('all');

  // Group tasks by category
  const tasksByCategory = tasks.reduce((acc, task) => {
    const category = task.category || 'Uncategorized';
    if (!acc[category]) acc[category] = [];
    acc[category].push(task);
    return acc;
  }, {} as Record<string, ServiceTask[]>);

  // Filter tasks
  const filteredTasksByCategory = Object.entries(tasksByCategory).reduce((acc, [category, categoryTasks]) => {
    const filtered = filterStatus === 'all'
      ? categoryTasks
      : categoryTasks.filter(t => t.status === filterStatus);
    if (filtered.length > 0) acc[category] = filtered;
    return acc;
  }, {} as Record<string, ServiceTask[]>);

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const toggleTaskStatus = (task: ServiceTask) => {
    const nextStatus: ServiceTaskStatus =
      task.status === 'not_started' ? 'in_progress' :
      task.status === 'in_progress' ? 'completed' :
      'not_started';
    onTaskStatusChange(task.id, nextStatus);
  };

  const totalTasks = tasks.length;
  const completedTasks = tasks.filter(t => t.status === 'completed').length;

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-medium text-gray-900">
            Tasks ({completedTasks}/{totalTasks} completed)
          </h3>
          <button
            onClick={onAddTask}
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md"
          >
            <Plus className="w-4 h-4 mr-1" />
            Add Task
          </button>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Filter:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as ServiceTaskStatus | 'all')}
            className="text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="all">All</option>
            <option value="not_started">Not Started</option>
            <option value="in_progress">In Progress</option>
            <option value="blocked">Blocked</option>
            <option value="completed">Completed</option>
            <option value="deferred">Deferred</option>
            <option value="not_applicable">N/A</option>
          </select>
        </div>
      </div>

      <div className="divide-y divide-gray-100">
        {Object.entries(filteredTasksByCategory).map(([category, categoryTasks]) => {
          const isExpanded = expandedCategories.has(category) || expandedCategories.size === 0;
          const completedInCategory = categoryTasks.filter(t => t.status === 'completed').length;
          const categoryColor = CATEGORY_COLORS[category] || 'bg-gray-100 text-gray-700';

          return (
            <div key={category}>
              <button
                onClick={() => toggleCategory(category)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50"
              >
                <div className="flex items-center gap-2">
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  )}
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${categoryColor}`}>
                    {category}
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {completedInCategory}/{categoryTasks.length}
                </span>
              </button>

              {isExpanded && (
                <div className="pb-2">
                  {categoryTasks.map((task) => {
                    const statusConfig = STATUS_CONFIG[task.status];
                    const StatusIcon = statusConfig.icon;

                    return (
                      <div
                        key={task.id}
                        className="px-4 py-2 flex items-start gap-3 hover:bg-gray-50 cursor-pointer group"
                      >
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleTaskStatus(task);
                          }}
                          className="mt-0.5 flex-shrink-0"
                        >
                          <StatusIcon className={`w-5 h-5 ${statusConfig.color}`} />
                        </button>

                        <div
                          className="flex-1 min-w-0"
                          onClick={() => onTaskClick(task)}
                        >
                          <div className="flex items-center gap-2">
                            <span className={`text-sm ${
                              task.status === 'completed' ? 'text-gray-500 line-through' : 'text-gray-900'
                            }`}>
                              {task.title}
                            </span>
                            {!task.is_required && (
                              <span className="text-xs text-gray-400">(optional)</span>
                            )}
                          </div>

                          <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                            {task.team && <span>{task.team}</span>}
                            {task.days_required && <span>{task.days_required}d</span>}
                            {task.target_start_date && (
                              <span>Start: {new Date(task.target_start_date).toLocaleDateString()}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}

        {Object.keys(filteredTasksByCategory).length === 0 && (
          <div className="px-4 py-8 text-center text-gray-500">
            No tasks match the selected filter.
          </div>
        )}
      </div>
    </div>
  );
}
