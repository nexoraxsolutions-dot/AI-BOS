'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../../context/AuthContext';
import {
  getEnvironmentVariables,
  createEnvironmentVariable,
  updateEnvironmentVariable,
  deleteEnvironmentVariable,
  exportEnvironmentVariables,
} from '../../../lib/api';

interface EnvironmentVariable {
  id: number;
  key: string;
  value?: string;
  masked_value?: string;
  description?: string;
  is_secret: boolean;
  created_at: string;
  updated_at: string;
}

export default function EnvironmentVariablesPage() {
  const { isAuthenticated, logout } = useAuth();
  const router = useRouter();
  const [envVars, setEnvVars] = useState<EnvironmentVariable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState<number | null>(null);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [exportedData, setExportedData] = useState<Record<string, string>>({});

  // Form state
  const [formData, setFormData] = useState({
    key: '',
    value: '',
    description: '',
    is_secret: false,
  });

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/');
      return;
    }
    loadEnvironmentVariables();
  }, [isAuthenticated, router]);

  const loadEnvironmentVariables = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getEnvironmentVariables();
      setEnvVars(data);
    } catch (err) {
      setError('Failed to load environment variables');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createEnvironmentVariable(formData);
      setFormData({ key: '', value: '', description: '', is_secret: false });
      setIsCreating(false);
      await loadEnvironmentVariables();
    } catch (err) {
      setError('Failed to create environment variable');
      console.error(err);
    }
  };

  const handleUpdate = async (id: number) => {
    try {
      await updateEnvironmentVariable(id, formData);
      setEditingId(null);
      setFormData({ key: '', value: '', description: '', is_secret: false });
      await loadEnvironmentVariables();
    } catch (err) {
      setError('Failed to update environment variable');
      console.error(err);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteEnvironmentVariable(id);
      setShowDeleteDialog(null);
      await loadEnvironmentVariables();
    } catch (err) {
      setError('Failed to delete environment variable');
      console.error(err);
    }
  };

  const handleExport = async () => {
    try {
      const data = await exportEnvironmentVariables();
      setExportedData(data);
      setShowExportDialog(true);
    } catch (err) {
      setError('Failed to export environment variables');
      console.error(err);
    }
  };

  const startEdit = (envVar: EnvironmentVariable) => {
    setEditingId(envVar.id);
    setFormData({
      key: envVar.key,
      value: envVar.value || '',
      description: envVar.description || '',
      is_secret: envVar.is_secret,
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setFormData({ key: '', value: '', description: '', is_secret: false });
  };

  const downloadEnvFile = () => {
    const content = Object.entries(exportedData)
      .map(([key, value]) => `${key}=${value}`)
      .join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '.env';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="flex items-center justify-center h-64">
            <div className="text-cyan-400 text-xl animate-pulse">Loading environment variables...</div>
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
            <h2 className="text-2xl font-semibold text-red-400 mb-2">Error Loading Environment Variables</h2>
            <p className="text-slate-300">{error}</p>
            <button
              onClick={() => router.push('/dashboard')}
              className="mt-6 rounded-xl bg-slate-800 px-6 py-3 text-white hover:bg-slate-700 transition"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="text-4xl font-semibold mt-2">Environment Variables</h1>
            <p className="text-slate-400 mt-1">Manage application configuration and secrets</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push('/dashboard')}
              className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
            >
              Dashboard
            </button>
            <button
              onClick={handleLogout}
              className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
            >
              Sign Out
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-2">
          <button
            onClick={handleExport}
            className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
          >
            Export .env
          </button>
          <button
            onClick={() => setIsCreating(true)}
            className="rounded-xl border border-cyan-500 bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-700 transition"
          >
            Add Variable
          </button>
        </div>

        {error && (
          <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Create Form */}
        {isCreating && (
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">
              Create Environment Variable
            </h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300">
                  Key
                </label>
                <input
                  type="text"
                  value={formData.key}
                  onChange={(e) =>
                    setFormData({ ...formData, key: e.target.value.toUpperCase() })
                  }
                  className="mt-1 block w-full rounded-md border-slate-600 bg-slate-800 text-white shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-3 py-2 border"
                  placeholder="DATABASE_URL"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300">
                  Value
                </label>
                <textarea
                  value={formData.value}
                  onChange={(e) =>
                    setFormData({ ...formData, value: e.target.value })
                  }
                  rows={3}
                  className="mt-1 block w-full rounded-md border-slate-600 bg-slate-800 text-white shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-3 py-2 border"
                  placeholder="postgresql://user:pass@localhost:5432/db"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300">
                  Description
                </label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  className="mt-1 block w-full rounded-md border-slate-600 bg-slate-800 text-white shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-3 py-2 border"
                  placeholder="Database connection URL"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_secret"
                  checked={formData.is_secret}
                  onChange={(e) =>
                    setFormData({ ...formData, is_secret: e.target.checked })
                  }
                  className="h-4 w-4 text-cyan-600 focus:ring-cyan-500 border-slate-600 rounded bg-slate-800"
                />
                <label
                  htmlFor="is_secret"
                  className="ml-2 block text-sm text-slate-300"
                >
                  Secret (value will be masked)
                </label>
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsCreating(false);
                    setFormData({ key: '', value: '', description: '', is_secret: false });
                  }}
                  className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl border border-cyan-500 bg-cyan-600 px-4 py-2 text-sm text-white hover:bg-cyan-700 transition"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Environment Variables List */}
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
          {envVars.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              No environment variables found. Create one to get started.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-900/50">
                  <tr>
                    <th className="px-8 py-4 text-left text-sm font-medium text-slate-300">Key</th>
                    <th className="px-8 py-4 text-left text-sm font-medium text-slate-300">Value</th>
                    <th className="px-8 py-4 text-left text-sm font-medium text-slate-300">Description</th>
                    <th className="px-8 py-4 text-left text-sm font-medium text-slate-300">Secret</th>
                    <th className="px-8 py-4 text-right text-sm font-medium text-slate-300">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {envVars.map((envVar) => (
                    <tr key={envVar.id} className="hover:bg-white/5 transition">
                      <td className="px-8 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-white">
                          {envVar.key}
                        </div>
                      </td>
                      <td className="px-8 py-4">
                        {editingId === envVar.id ? (
                          <input
                            type="text"
                            value={formData.value}
                            onChange={(e) =>
                              setFormData({ ...formData, value: e.target.value })
                            }
                            className="block w-full rounded-md border-slate-600 bg-slate-800 text-white shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-2 py-1 border"
                          />
                        ) : (
                          <div className="text-sm text-slate-300">
                            {envVar.is_secret
                              ? envVar.masked_value || '****'
                              : envVar.value}
                          </div>
                        )}
                      </td>
                      <td className="px-8 py-4">
                        <div className="text-sm text-slate-400">
                          {envVar.description || '-'}
                        </div>
                      </td>
                      <td className="px-8 py-4 whitespace-nowrap">
                        {envVar.is_secret ? (
                          <span className="inline-flex rounded-full px-3 py-1 text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/30">
                            Yes
                          </span>
                        ) : (
                          <span className="inline-flex rounded-full px-3 py-1 text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/30">
                            No
                          </span>
                        )}
                      </td>
                      <td className="px-8 py-4 whitespace-nowrap text-right text-sm font-medium">
                        {editingId === envVar.id ? (
                          <div className="space-x-2">
                            <button
                              onClick={() => handleUpdate(envVar.id)}
                              className="text-cyan-400 hover:text-cyan-300"
                            >
                              Save
                            </button>
                            <button
                              onClick={cancelEdit}
                              className="text-slate-400 hover:text-slate-300"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <div className="space-x-2">
                            <button
                              onClick={() => startEdit(envVar)}
                              className="text-cyan-400 hover:text-cyan-300"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => setShowDeleteDialog(envVar.id)}
                              className="text-red-400 hover:text-red-300"
                            >
                              Delete
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteDialog && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center z-50">
          <div className="rounded-2xl border border-white/10 bg-slate-900 p-6 max-w-md w-full">
            <h3 className="text-xl font-semibold text-white mb-4">
              Delete Environment Variable
            </h3>
            <p className="text-sm text-slate-300 mb-6">
              Are you sure you want to delete this environment variable? This action
              cannot be undone.
            </p>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowDeleteDialog(null)}
                className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 hover:text-white transition"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(showDeleteDialog)}
                className="rounded-xl border border-red-500 bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700 transition"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Export Dialog */}
      {showExportDialog && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center z-50">
          <div className="rounded-2xl border border-white/10 bg-slate-900 p-6 max-w-2xl w-full max-h-screen overflow-y-auto">
            <h3 className="text-xl font-semibold text-white mb-4">
              Export Environment Variables
            </h3>
            <pre className="bg-slate-800 p-4 rounded-lg text-sm overflow-x-auto mb-4 text-slate-300">
              {Object.entries(exportedData)
                .map(([key, value]) => `${key}=${value}`)
                .join('\n')}
            </pre>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowExportDialog(false)}
                className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 hover:text-white transition"
              >
                Close
              </button>
              <button
                onClick={downloadEnvFile}
                className="rounded-xl border border-cyan-500 bg-cyan-600 px-4 py-2 text-sm text-white hover:bg-cyan-700 transition"
              >
                Download .env
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}