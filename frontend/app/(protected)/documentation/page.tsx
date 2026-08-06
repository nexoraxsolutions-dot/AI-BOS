"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../context/AuthContext'
import {
  getDocuments,
  getDocumentStats,
  createDocument,
  updateDocument,
  deleteDocument,
  publishDocument,
  Document,
  DocumentCreate,
  DocumentUpdate,
  DocumentStats,
} from '../../../lib/api'

const STATUS_STYLES: Record<string, string> = {
  published: 'bg-green-500/10 text-green-400 border border-green-500/30',
  draft: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30',
  archived: 'bg-slate-500/10 text-slate-400 border border-slate-500/30',
}

export default function DocumentationPage() {
  const { isAuthenticated, logout, user } = useAuth()
  const router = useRouter()
  const [documents, setDocuments] = useState<Document[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<DocumentStats | null>(null)

  // Search & filter state
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sortBy, setSortBy] = useState('title')
  const [sortOrder, setSortOrder] = useState('asc')

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Create form
  const [createForm, setCreateForm] = useState<DocumentCreate>({
    title: '',
    slug: '',
    summary: '',
    content: '',
    category: 'general',
    tags: '',
    status: 'draft',
    company_id: null,
  })

  // Edit form
  const [editForm, setEditForm] = useState<DocumentUpdate>({})

  const isSuperuser = !!user?.is_superuser

  const fetchData = async () => {
    try {
      setLoading(true)
      const [listResponse, statsData] = await Promise.all([
        getDocuments({
          skip: (page - 1) * pageSize,
          limit: pageSize,
          search: search || undefined,
          category: categoryFilter || undefined,
          status: statusFilter || undefined,
          sort_by: sortBy,
          sort_order: sortOrder,
        }),
        getDocumentStats(),
      ])
      setDocuments(listResponse.items)
      setTotal(listResponse.total)
      setStats(statsData)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
    fetchData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, router, page, sortBy, sortOrder])

  // Debounce search & filters
  useEffect(() => {
    const timer = setTimeout(() => {
      if (isAuthenticated) {
        setPage(1)
        fetchData()
      }
    }, 500)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, categoryFilter, statusFilter])

  const totalPages = Math.ceil(total / pageSize)

  const handleCreate = async () => {
    setFormError(null)
    setSubmitting(true)
    try {
      await createDocument({
        ...createForm,
        slug: createForm.slug?.trim() ? createForm.slug.trim() : undefined,
        company_id: createForm.company_id || null,
      })
      setShowCreateModal(false)
      setCreateForm({
        title: '',
        slug: '',
        summary: '',
        content: '',
        category: 'general',
        tags: '',
        status: 'draft',
        company_id: null,
      })
      setPage(1)
      fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create document')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = async () => {
    if (!selectedDocument) return
    setFormError(null)
    setSubmitting(true)
    try {
      await updateDocument(selectedDocument.id, {
        ...editForm,
        slug: editForm.slug?.trim() ? editForm.slug.trim() : undefined,
        company_id: editForm.company_id || null,
      })
      setShowEditModal(false)
      setSelectedDocument(null)
      setEditForm({})
      fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update document')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedDocument) return
    setFormError(null)
    setSubmitting(true)
    try {
      await deleteDocument(selectedDocument.id)
      setShowDeleteModal(false)
      setSelectedDocument(null)
      fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to delete document')
    } finally {
      setSubmitting(false)
    }
  }

  const handlePublish = async (doc: Document) => {
    if (doc.status === 'published') return
    setFormError(null)
    setSubmitting(true)
    try {
      await publishDocument(doc.id)
      fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to publish document')
    } finally {
      setSubmitting(false)
    }
  }

  const openEditModal = (doc: Document) => {
    setSelectedDocument(doc)
    setEditForm({
      title: doc.title,
      slug: doc.slug || '',
      summary: doc.summary || '',
      content: doc.content || '',
      category: doc.category || 'general',
      tags: doc.tags || '',
      status: doc.status || 'draft',
      company_id: doc.company_id ?? null,
      is_active: doc.is_active,
    })
    setFormError(null)
    setShowEditModal(true)
  }

  const openDeleteModal = (doc: Document) => {
    setSelectedDocument(doc)
    setFormError(null)
    setShowDeleteModal(true)
  }

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  if (loading && documents.length === 0) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-7xl">
          <div className="flex items-center justify-center h-64">
            <div className="text-cyan-400 text-xl animate-pulse">Loading documentation...</div>
          </div>
        </div>
      </main>
    )
  }

  if (error && documents.length === 0) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-7xl">
          <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
            <h2 className="text-2xl font-semibold text-red-400 mb-2">Error Loading Documentation</h2>
            <p className="text-slate-300 mb-6">{error}</p>
            <button
              onClick={() => router.push('/dashboard')}
              className="mt-6 rounded-xl bg-slate-800 px-6 py-3 text-white hover:bg-slate-700 transition"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </main>
    )
  }

  const categories = stats
    ? Object.keys(stats.documents_by_category).sort()
    : []

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="text-4xl font-semibold mt-2">Documentation</h1>
            <p className="text-slate-400 mt-1">Manage the knowledge base and documentation articles</p>
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

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-5">
              <p className="text-slate-400 text-sm">Total Documents</p>
              <p className="text-3xl font-semibold text-white mt-1">{stats.total_documents}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-5">
              <p className="text-slate-400 text-sm">Published</p>
              <p className="text-3xl font-semibold text-green-400 mt-1">{stats.published_documents}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-5">
              <p className="text-slate-400 text-sm">Draft</p>
              <p className="text-3xl font-semibold text-yellow-400 mt-1">{stats.draft_documents}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-5">
              <p className="text-slate-400 text-sm">Archived</p>
              <p className="text-3xl font-semibold text-slate-400 mt-1">{stats.archived_documents}</p>
            </div>
          </div>
        )}


        {/* Controls: Search, Filters, Create Button */}
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-slate-400 mb-1">Search</label>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by title, summary, content, tags..."
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
            >
              <option value="">All Statuses</option>
              <option value="published">Published</option>
              <option value="draft">Draft</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
            >
              <option value="title">Title</option>
              <option value="category">Category</option>
              <option value="status">Status</option>
              <option value="updated_at">Updated</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Order</label>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
            >
              <option value="asc">Asc</option>
              <option value="desc">Desc</option>
            </select>
          </div>
          {isSuperuser && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="rounded-xl bg-cyan-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-cyan-500 transition"
            >
              + Create Document
            </button>
          )}
          <button
            onClick={fetchData}
            className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
          >
            Refresh
          </button>
        </div>


        {/* Documents Table */}
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
          <div className="px-8 py-6 border-b border-white/10">
            <h2 className="text-2xl font-semibold">All Documents ({total})</h2>
          </div>

          {documents.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              No documents found. Create your first document to get started.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-900/50">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">ID</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Title</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Category</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Status</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Version</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Author</th>
                    {isSuperuser && <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-white/5 transition">
                      <td className="px-6 py-4 text-sm text-slate-400">{doc.id}</td>
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-white font-medium">{doc.title}</div>
                          {doc.summary && (
                            <div className="text-xs text-slate-400 mt-0.5 max-w-md truncate">{doc.summary}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-300">
                        {doc.category || <span className="text-slate-600">general</span>}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                          STATUS_STYLES[doc.status || 'draft'] || STATUS_STYLES.draft
                        }`}>
                          {(doc.status || 'draft').charAt(0).toUpperCase() + (doc.status || 'draft').slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-300">
                        {doc.version !== undefined && doc.version !== null ? doc.version : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-300">
                        {doc.author_name || <span className="text-slate-600">—</span>}
                      </td>
                      {isSuperuser && (
                        <td className="px-6 py-4">
                          <div className="flex gap-2 flex-wrap">
                            {doc.status !== 'published' && (
                              <button
                                onClick={() => handlePublish(doc)}
                                disabled={submitting}
                                className="rounded-lg bg-green-600/20 px-3 py-1.5 text-xs text-green-400 hover:bg-green-600/40 transition disabled:opacity-50"
                              >
                                Publish
                              </button>
                            )}
                            <button
                              onClick={() => openEditModal(doc)}
                              className="rounded-lg bg-blue-600/20 px-3 py-1.5 text-xs text-blue-400 hover:bg-blue-600/40 transition"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => openDeleteModal(doc)}
                              className="rounded-lg bg-red-600/20 px-3 py-1.5 text-xs text-red-400 hover:bg-red-600/40 transition"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}


          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-8 py-4 border-t border-white/10 flex items-center justify-between">
              <p className="text-sm text-slate-400">
                Showing {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, total)} of {total}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  Previous
                </button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  const start = Math.max(1, Math.min(page - 2, totalPages - 4))
                  const p = start + i
                  return (
                    <button
                      key={p}
                      onClick={() => setPage(p)}
                      className={`rounded-lg px-3 py-1.5 text-sm transition ${
                        p === page
                          ? 'bg-cyan-600 text-white'
                          : 'border border-slate-700 bg-slate-900 text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      {p}
                    </button>
                  )
                })}
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>


      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm overflow-y-auto">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-2xl m-4 my-8">
            <div className="px-8 py-6 border-b border-white/10">
              <h2 className="text-2xl font-semibold">Create Document</h2>
            </div>
            <div className="px-8 py-6 space-y-4">
              {formError && (
                <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-red-400 text-sm">{formError}</div>
              )}
              <div>
                <label className="block text-sm text-slate-300 mb-1">Title *</label>
                <input
                  type="text"
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  placeholder="Document title"
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Slug</label>
                <input
                  type="text"
                  value={createForm.slug || ''}
                  onChange={(e) => setCreateForm({ ...createForm, slug: e.target.value })}
                  placeholder="optional-url-slug"
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Summary</label>
                <textarea
                  value={createForm.summary || ''}
                  onChange={(e) => setCreateForm({ ...createForm, summary: e.target.value })}
                  placeholder="Short summary of the document"
                  rows={2}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Content</label>
                <textarea
                  value={createForm.content || ''}
                  onChange={(e) => setCreateForm({ ...createForm, content: e.target.value })}
                  placeholder="Full document content"
                  rows={6}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Category</label>
                  <select
                    value={createForm.category || 'general'}
                    onChange={(e) => setCreateForm({ ...createForm, category: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                  >
                    <option value="general">General</option>
                    <option value="tutorial">Tutorial</option>
                    <option value="guide">Guide</option>
                    <option value="reference">Reference</option>
                    <option value="api">API</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Status</label>
                  <select
                    value={createForm.status || 'draft'}
                    onChange={(e) => setCreateForm({ ...createForm, status: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                  >
                    <option value="draft">Draft</option>
                    <option value="published">Published</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Tags</label>
                <input
                  type="text"
                  value={createForm.tags || ''}
                  onChange={(e) => setCreateForm({ ...createForm, tags: e.target.value })}
                  placeholder="Comma separated tags"
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                />
              </div>
            </div>
            <div className="px-8 py-4 border-t border-white/10 flex justify-end gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="rounded-xl border border-slate-700 bg-slate-900 px-6 py-2.5 text-sm text-slate-300 hover:bg-slate-800 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={submitting || !createForm.title.trim()}
                className="rounded-xl bg-cyan-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-cyan-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Creating...' : 'Create Document'}
              </button>
            </div>
          </div>
        </div>
      )}


      {/* Edit Modal */}
      {showEditModal && selectedDocument && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm overflow-y-auto">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-2xl m-4 my-8">
            <div className="px-8 py-6 border-b border-white/10">
              <h2 className="text-2xl font-semibold">Edit Document</h2>
            </div>
            <div className="px-8 py-6 space-y-4">
              {formError && (
                <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-red-400 text-sm">{formError}</div>
              )}
              <div>
                <label className="block text-sm text-slate-300 mb-1">Title</label>
                <input
                  type="text"
                  value={editForm.title || ''}
                  onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Slug</label>
                <input
                  type="text"
                  value={editForm.slug || ''}
                  onChange={(e) => setEditForm({ ...editForm, slug: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Summary</label>
                <textarea
                  value={editForm.summary || ''}
                  onChange={(e) => setEditForm({ ...editForm, summary: e.target.value })}
                  rows={2}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Content</label>
                <textarea
                  value={editForm.content || ''}
                  onChange={(e) => setEditForm({ ...editForm, content: e.target.value })}
                  rows={6}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Category</label>
                  <select
                    value={editForm.category || 'general'}
                    onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                  >
                    <option value="general">General</option>
                    <option value="tutorial">Tutorial</option>
                    <option value="guide">Guide</option>
                    <option value="reference">Reference</option>
                    <option value="api">API</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Status</label>
                  <select
                    value={editForm.status || 'draft'}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                  >
                    <option value="draft">Draft</option>
                    <option value="published">Published</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
              </div>


              <div>
                <label className="block text-sm text-slate-300 mb-1">Tags</label>
                <input
                  type="text"
                  value={editForm.tags || ''}
                  onChange={(e) => setEditForm({ ...editForm, tags: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Active</label>
                <select
                  value={editForm.is_active ? 'active' : 'inactive'}
                  onChange={(e) => setEditForm({ ...editForm, is_active: e.target.value === 'active' })}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>
            <div className="px-8 py-4 border-t border-white/10 flex justify-end gap-3">
              <button
                onClick={() => setShowEditModal(false)}
                className="rounded-xl border border-slate-700 bg-slate-900 px-6 py-2.5 text-sm text-slate-300 hover:bg-slate-800 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleEdit}
                disabled={submitting}
                className="rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && selectedDocument && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-md m-4">
            <div className="px-8 py-6 border-b border-white/10">
              <h2 className="text-2xl font-semibold text-red-400">Delete Document</h2>
            </div>
            <div className="px-8 py-6">
              {formError && (
                <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-red-400 text-sm mb-4">{formError}</div>
              )}
              <p className="text-slate-300">
                Are you sure you want to delete <strong className="text-white">{selectedDocument.title}</strong>?
              </p>
              <p className="text-slate-400 text-sm mt-2">This action cannot be undone.</p>
            </div>
            <div className="px-8 py-4 border-t border-white/10 flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="rounded-xl border border-slate-700 bg-slate-900 px-6 py-2.5 text-sm text-slate-300 hover:bg-slate-800 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={submitting}
                className="rounded-xl bg-red-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-red-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Deleting...' : 'Delete Document'}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}

