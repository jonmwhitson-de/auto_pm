import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, Loader2 } from 'lucide-react';
import { createProject, uploadProject } from '../api/client';

type InputMode = 'text' | 'file';

export default function NewProjectPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<InputMode>('text');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [prdContent, setPrdContent] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      navigate(`/projects/${project.id}`);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: uploadProject,
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      navigate(`/projects/${project.id}`);
    },
  });

  const isLoading = createMutation.isPending || uploadMutation.isPending;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    if (mode === 'text') {
      if (!prdContent.trim()) return;
      createMutation.mutate({ name, description, prd_content: prdContent });
    } else {
      if (!file) return;
      const formData = new FormData();
      formData.append('name', name);
      formData.append('description', description);
      formData.append('file', file);
      uploadMutation.mutate(formData);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Create New Project</h1>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex gap-4 mb-6">
          <button
            type="button"
            onClick={() => setMode('text')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border-2 transition ${
              mode === 'text'
                ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                : 'border-gray-200 text-gray-600 hover:border-gray-300'
            }`}
          >
            <FileText className="w-5 h-5" />
            Paste PRD Text
          </button>
          <button
            type="button"
            onClick={() => setMode('file')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border-2 transition ${
              mode === 'file'
                ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                : 'border-gray-200 text-gray-600 hover:border-gray-300'
            }`}
          >
            <Upload className="w-5 h-5" />
            Upload Word Doc
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Project Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="My Project"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Brief project description"
            />
          </div>

          {mode === 'text' ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                PRD Content *
              </label>
              <textarea
                value={prdContent}
                onChange={(e) => setPrdContent(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 h-64 font-mono text-sm"
                placeholder="Paste your Product Requirements Document here..."
                required
              />
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Word Document *
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <input
                  type="file"
                  accept=".docx"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer flex flex-col items-center"
                >
                  <Upload className="w-10 h-10 text-gray-400 mb-2" />
                  {file ? (
                    <span className="text-indigo-600 font-medium">{file.name}</span>
                  ) : (
                    <>
                      <span className="text-indigo-600 font-medium">Click to upload</span>
                      <span className="text-sm text-gray-500">.docx files only</span>
                    </>
                  )}
                </label>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Creating...
              </>
            ) : (
              'Create Project'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
