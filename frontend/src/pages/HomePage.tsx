import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { FolderOpen, Plus, Loader2 } from 'lucide-react';
import { getProjects } from '../api/client';

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  analyzing: 'bg-yellow-100 text-yellow-800',
  ready: 'bg-green-100 text-green-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-purple-100 text-purple-800',
};

export default function HomePage() {
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!projects || projects.length === 0) {
    return (
      <div className="text-center py-16">
        <FolderOpen className="w-16 h-16 mx-auto text-gray-400 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No projects yet</h2>
        <p className="text-gray-600 mb-6">
          Create your first project by uploading a PRD
        </p>
        <Link
          to="/projects/new"
          className="inline-flex items-center gap-2 bg-indigo-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-indigo-700 transition"
        >
          <Plus className="w-5 h-5" />
          New Project
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Projects</h1>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {projects.map(project => (
          <Link
            key={project.id}
            to={`/projects/${project.id}`}
            className="block bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition"
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="text-lg font-semibold text-gray-900">{project.name}</h3>
              <span className={`text-xs px-2 py-1 rounded-full ${statusColors[project.status]}`}>
                {project.status.replace('_', ' ')}
              </span>
            </div>
            {project.description && (
              <p className="text-sm text-gray-600 line-clamp-2">{project.description}</p>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
