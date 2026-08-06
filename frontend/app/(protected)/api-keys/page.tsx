"use client"

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../../context/AuthContext'
import { useRouter } from 'next/navigation'
import {
  getApiKeys,
  createApiKey,
  updateApiKey,
  deleteApiKey,
  revokeApiKey,
  ApiKeyInfo,
  ApiKeyListResponse,
  ApiKeyCreateResponse
} from '../../../lib/api'

export default function ApiKeysPage() {
  const { isAuthenticated, token } = useAuth()
  const router = useRouter()
  const [apiKeys, setApiKeys] = useState<ApiKeyInfo[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [includeInactive, setIncludeInactive] = useState(false)

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showRevokeConfirm, setShowRevokeConfirm] = useState(false)
  const [selectedKey, setSelectedKey] = useState<ApiKeyInfo | null>(null)
  const [newApiKey, setNewApiKey] = useState<string | null>(null)

  // Form states
  const [keyName, setKeyName] = useState('')
  const [permissions, setPermissions] = useState('')
  const [expiresAt, setExpiresAt] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const fetchApiKeys = useCallback(async () => {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      const data = await getApiKeys((page - 1) * pageSize, pageSize, includeInactive)
      setApiKeys(data.items)
      setTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load API keys')
    } finally {
      setLoading(false)
    }
  }, [token, page, pageSize, includeInactive])

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }
    fetchApiKeys()
  }, [isAuthenticated, router, fetchApiKeys])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    setSuccess('')
    try {
      const data = await createApiKey({
        key_name: keyName,
        permissions: permissions || undefined,
        expires_at: expiresAt || undefined,
      })
      setNewApiKey(data.api_key)
      setSuccess('API key created successfully! Make sure to copy it now - it will not be shown again.')
      setShowCreateModal(false)
      setKeyName('')
      setPermissions('')
      setExpiresAt('')
      fetchApiKeys()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create API key')
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedKey) return
    setSubmitting(true)
    setError('')
    try {
      await updateApiKey(selectedKey.id, {
        key_name: keyName || undefined,
        permissions: permissions || undefined,
        expires_at: expiresAt || undefined,
        is_active: selectedKey.is_active,
      })
      setSuccess('API key updated successfully')
      setShowEditModal(false)
      setSelectedKey(null)
      setKeyName('')
      setPermissions('')
      setExpiresAt('')
      fetchApiKeys()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update API key')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedKey) return
    setSubmitting(true)
    setError('')
    try {
      await deleteApiKey(selectedKey.id)
      setSuccess('API key deleted successfully')
      setShowDeleteConfirm(false)
      setSelectedKey(null)
      fetchApiKeys()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete API key')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRevoke = async () => {
    if (!selectedKey) return
    setSubmitting(true)
    setError('')
    try {
      await revokeApiKey(selectedKey.id)
      setSuccess('API key revoked successfully')
      setShowRevokeConfirm(false)
      setSelectedKey(null)
      fetchApiKeys()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke API key')
    } finally {
      setSubmitting(false)
    }
  }

  const openEditModal = (apiKey: ApiKeyInfo) => {
    setSelectedKey(apiKey)
    setKeyName(apiKey.key_name)
    setPermissions(apiKey.permissions || '')
    setExpiresAt(apiKey.expires_at ? apiKey.expires_at.split('T')[0] : '')
    setShowEditModal(true)
  }

  const openDeleteConfirm = (apiKey: ApiKeyInfo) => {
    setSelectedKey(apiKey)
    setShowDeleteConfirm(true)
  }

  const openRevokeConfirm = (apiKey: ApiKeyInfo) => {
    setSelectedKey(apiKey)
    setShowRevokeConfirm(true)
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleString()
  }

  const isExpired = (expiresAt: string | undefined) => {
    return expiresAt ? new Date(expiresAt) < new Date() : false
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-white">API Keys</h1>
            <p className="mt-2 text-slate-400">Manage API keys for programmatic access to the API</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="rounded-xl bg-cyan-600 px-4 py-2 text-sm text-white hover:bg-cyan-500 transition"
          >
            Create API Key
          </button>
        </div>

        {error && (
          <div className="mb-6 rounded-xl bg-red-500/10 border border-red-500/30 p-4">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-6 rounded-xl bg-green-500/10 border border-green-500/30 p-4">
            <p className="text-sm text-green-400">{success}</p>
          </div>
        )}

        {newApiKey && (
          <div className="mb-6 rounded-xl bg-yellow-500/10 border border-yellow-500/30 p-4">
            <p className="text-sm text-yellow-400 font-mono break-all">
              <strong>Your new API key (save this now):</strong> {newApiKey}
            </p>
            <button
              onClick={() => setNewApiKey(null)}
              className="mt-2 text-xs text-yellow-300 hover:text-yellow-200"
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="mb-6 flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => {
                setIncludeInactive(e.target.checked)
                setPage(1)
              }}
              className="rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-cyan-500/20"
            />
            Include inactive keys
          </label>
          <span className="text-sm text-slate-500">
            {total} key{total !== 1 ? 's' : ''} found
          </span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent" />
          </div>
        ) : apiKeys.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-12 text-center">
            <p className="text-slate-400">No API keys found</p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-white/10">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 bg-slate-900/80">
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">ID</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Name</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Status</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Created</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Last Used</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Expires</th>
                  <th className="px-4 py-3 text-right text-slate-400 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {apiKeys.map((k) => {
                  const expired = isExpired(k.expires_at)
                  return (
                    <tr key={k.id} className="border-b border-white/5 hover:bg-white/5 transition">
                      <td className="px-4 py-3 text-slate-300">{k.id}</td>
                      <td className="px-4 py-3 text-slate-300">{k.key_name}</td>
                      <td className="px-4 py-3">
                        {!k.is_active ? (
                          <span className="rounded-full bg-red-500/10 px-2.5 py-0.5 text-xs text-red-400">Revoked</span>
                        ) : expired ? (
                          <span className="rounded-full bg-yellow-500/10 px-2.5 py-0.5 text-xs text-yellow-400">Expired</span>
                        ) : (
                          <span className="rounded-full bg-green-500/10 px-2.5 py-0.5 text-xs text-green-400">Active</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-400">{formatDate(k.created_at)}</td>
                      <td className="px-4 py-3 text-slate-400">{formatDate(k.last_used_at)}</td>
                      <td className={`px-4 py-3 ${expired ? 'text-yellow-400' : 'text-slate-400'}`}>
                        {formatDate(k.expires_at)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-2">
                          {k.is_active && !expired && (
                            <>
                              <button
                                onClick={() => openEditModal(k)}
                                className="rounded-lg bg-cyan-500/10 px-3 py-1.5 text-xs text-cyan-400 hover:bg-cyan-500/20 transition"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => openRevokeConfirm(k)}
                                className="rounded-lg bg-yellow-500/10 px-3 py-1.5 text-xs text-yellow-400 hover:bg-yellow-500/20 transition"
                              >
                                Revoke
                              </button>
                            </>
                          )}
                          <button
                            onClick={() => openDeleteConfirm(k)}
                            className="rounded-lg bg-red-500/10 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/20 transition"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 transition disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-sm text-slate-400">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 transition disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}

        {/* Create Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
              <h3 className="text-lg font-semibold text-white">Create API Key</h3>
              <form onSubmit={handleCreate} className="mt-4 space-y-4">
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Key Name *</label>
                  <input
                    type="text"
                    value={keyName}
                    onChange={(e) => setKeyName(e.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                    placeholder="e.g., Production API Key"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Permissions (optional)</label>
                  <input
                    type="text"
                    value={permissions}
                    onChange={(e) => setPermissions(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                    placeholder="e.g., read,write"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Expires At (optional)</label>
                  <input
                    type="date"
                    value={expiresAt}
                    onChange={(e) => setExpiresAt(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <div className="flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateModal(false)
                      setKeyName('')
                      setPermissions('')
                      setExpiresAt('')
                    }}
                    className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="rounded-xl bg-cyan-600 px-4 py-2 text-sm text-white hover:bg-cyan-500 transition disabled:opacity-50"
                  >
                    {submitting ? 'Creating...' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Edit Modal */}
        {showEditModal && selectedKey && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
              <h3 className="text-lg font-semibold text-white">Edit API Key</h3>
              <form onSubmit={handleUpdate} className="mt-4 space-y-4">
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Key Name *</label>
                  <input
                    type="text"
                    value={keyName}
                    onChange={(e) => setKeyName(e.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Permissions (optional)</label>
                  <input
                    type="text"
                    value={permissions}
                    onChange={(e) => setPermissions(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Expires At (optional)</label>
                  <input
                    type="date"
                    value={expiresAt}
                    onChange={(e) => setExpiresAt(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <div className="flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowEditModal(false)
                      setSelectedKey(null)
                      setKeyName('')
                      setPermissions('')
                      setExpiresAt('')
                    }}
                    className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="rounded-xl bg-cyan-600 px-4 py-2 text-sm text-white hover:bg-cyan-500 transition disabled:opacity-50"
                  >
                    {submitting ? 'Saving...' : 'Save'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Delete Confirmation */}
        {showDeleteConfirm && selectedKey && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
              <h3 className="text-lg font-semibold text-white">Delete API Key</h3>
              <p className="mt-2 text-sm text-slate-400">
                Are you sure you want to delete the API key "{selectedKey.key_name}"? This action cannot be undone.
              </p>
              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false)
                    setSelectedKey(null)
                  }}
                  className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={submitting}
                  className="rounded-xl bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-500 transition disabled:opacity-50"
                >
                  {submitting ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Revoke Confirmation */}
        {showRevokeConfirm && selectedKey && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
              <h3 className="text-lg font-semibold text-white">Revoke API Key</h3>
              <p className="mt-2 text-sm text-slate-400">
                Are you sure you want to revoke the API key "{selectedKey.key_name}"? It will no longer work for API authentication.
              </p>
              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowRevokeConfirm(false)
                    setSelectedKey(null)
                  }}
                  className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRevoke}
                  disabled={submitting}
                  className="rounded-xl bg-yellow-600 px-4 py-2 text-sm text-white hover:bg-yellow-500 transition disabled:opacity-50"
                >
                  {submitting ? 'Revoking...' : 'Revoke'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}