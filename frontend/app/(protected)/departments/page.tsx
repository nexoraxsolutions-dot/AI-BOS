"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../context/AuthContext'
import { 
  getDepartments, getDepartmentStats, createDepartment, updateDepartment, deleteDepartment, 
  Department, DepartmentCreate, DepartmentUpdate, DepartmentStats 
} from '../../../lib/api'

export default function DepartmentsPage() {
  const { isAuthenticated, logout } = useAuth()
  const router = useRouter()
  const [departments, setDepartments] = useState<Department[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<DepartmentStats | null>(null)
  const [isSuperuser, setIsSuperuser] = useState(false)
  
  // Search & Filter state
  const [search, setSearch] = useState('')
  const [companyFilter, setCompanyFilter] = useState<string>('')
  const [isActiveFilter, setIsActiveFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState('name')
  const [sortOrder, setSortOrder] = useState('asc')

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [selectedDepartment, setSelectedDepartment] = useState<Department | null>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Create form
  const [createForm, setCreateForm] = useState<DepartmentCreate>({
    name: '',
    description: '',
    company_id: 0,
    manager_id: undefined,
    budget: '',
    location: '',
    is_active: true,
  })

  // Edit form
  const [editForm, setEditForm] = useState<DepartmentUpdate>({})

  const fetchData = async () => {
    try {
      setLoading(true)
      const [listResponse, statsData] = await Promise.all([
        getDepartments({
          skip: (page - 1) * pageSize,
          limit: pageSize,
          search: search || undefined,
          company_id: companyFilter ? parseInt(companyFilter) : undefined,
          is_active: isActiveFilter === 'all' ? undefined : isActiveFilter === 'active',
          sort_by: sortBy,
          sort_order: sortOrder,
        }),
        getDepartmentStats(),
      ])
      setDepartments(listResponse.items)
      setTotal(listResponse.total)
      setStats(statsData)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load departments')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }
    fetchData()
  }, [isAuthenticated, router, page, sortBy, sortOrder])

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (isAuthenticated) {
        setPage(1)
        fetchData()
      }
    }, 500)
    return () => clearTimeout(timer)
  }, [search, companyFilter, isActiveFilter])

  const totalPages = Math.ceil(total / pageSize)

  const handleCreate = async () => {
    setFormError(null)
    setSubmitting(true)
    try {
      await createDepartment(createForm)
      setShowCreateModal(false)
      setCreateForm({
        name: '',
        description: '',
        company_id: 0,
        manager_id: undefined,
        budget: '',
        location: '',
        is_active: true,
      })
      fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create department')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = async () => {
    if (!selectedDepartment) return
    setFormError(null)
    setSubmitting(true)
    try {
      await updateDepartment(selectedDepartment.id, editForm)
      setShowEditModal(false)
      setSelectedDepartment(null)
      setEditForm({})
      fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update department')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedDepartment) return
    setFormError(null)
    setSubmitting(true)
    try {
      await deleteDepartment(selectedDepartment.id)
      setShowDeleteModal(false)
      setSelectedDepartment(null)
      fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to delete department')
    } finally {
      setSubmitting(false)
    }
  }

  const openEditModal = (department: Department) => {
    setSelectedDepartment(department)
    setEditForm({
      name: department.name,
      description: department.description,
      manager_id: department.manager_id,
      budget: department.budget,
      location: department.location,
      is_active: department.is_active,
    })
    setFormError(null)
    setShowEditModal(true)
  }

  const openDeleteModal = (department: Department) => {
    setSelectedDepartment(department)
    setFormError(null)
    setShowDeleteModal(true)
  }

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  if (loading && departments.length === 0) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="flex items-center justify-center h-64">
            <div className="text-cyan-400 text-xl animate-pulse">Loading departments...</div>
          </div>
        </div>
      </main>
    )
  }

  if (error && departments.length === 0) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
            <h2 className="text-2xl font-semibold text-red-400 mb-2">Error Loading Departments</h2>
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
    )
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="text-4xl font-semibold mt-2">Departments Management</h1>
            <p className="text-slate-400 mt-1">Organize and manage company departments</p>
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
              <p className="text-slate-400 text-sm">Total Departments</p>
              <p className="text-3xl font-semibold text-white mt-1">{stats.total_departments}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-5">
              <p className="text-slate-400 text-sm">Active</p>
              <p className="text-3xl font-semibold text-green-400 mt-1">{stats.active_departments}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-5">
              <p className="text-slate-400 text-sm">Companies with Departments</p>
              <p className="text-3xl font-semibold text-cyan-400 mt-1">{stats.total_companies_with_departments}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-5">
              <p className="text-slate-400 text-sm">Avg per Company</p>
              <p className="text-3xl font-semibold text-purple-400 mt-1">
                {stats.avg_departments_per_company ? Math.round(stats.avg_departments_per_company) : '—'}
              </p>
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
              placeholder="Search by name, description, location..."
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Company ID</label>
            <input
              type="number"
              value={companyFilter}
              onChange={(e) => setCompanyFilter(e.target.value)}
              placeholder="Filter by company"
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Status</label>
            <select
              value={isActiveFilter}
              onChange={(e) => setIsActiveFilter(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
            >
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
            >
              <option value="name">Name</option>
              <option value="created_at">Created</option>
              <option value="company_id">Company ID</option>
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
              + Create Department
            </button>
          )}
          <button
            onClick={fetchData}
            className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
          >
            Refresh
          </button>
        </div>

        {/* Departments Table */}
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
          <div className="px-8 py-6 border-b border-white/10">
            <h2 className="text-2xl font-semibold">All Departments ({total})</h2>
          </div>
          
          {departments.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              No departments found. Create your first department to get started.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-900/50">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">ID</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Name</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Company</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Manager</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Location</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Budget</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Status</th>
                    {isSuperuser && <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {departments.map((department) => (
                    <tr key={department.id} className="hover:bg-white/5 transition">
                      <td className="px-6 py-4 text-sm text-slate-400">{department.id}</td>
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-white font-medium">{department.name}</div>
                          {department.description && (
                            <div className="text-xs text-slate-400 mt-0.5 line-clamp-1">{department.description}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-300">
                        {department.company_name || <span className="text-slate-600">—</span>}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-300">
                        {department.manager_name || <span className="text-slate-600">—</span>}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-300">
                        {department.location || <span className="text-slate-600">—</span>}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-300">
                        {department.budget || <span className="text-slate-600">—</span>}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                          department.is_active
                            ? 'bg-green-500/10 text-green-400 border border-green-500/30'
                            : 'bg-red-500/10 text-red-400 border border-red-500/30'
                        }`}>
                          {department.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      {isSuperuser && (
                        <td className="px-6 py-4">
                          <div className="flex gap-2">
                            <button
                              onClick={() => openEditModal(department)}
                              className="rounded-lg bg-blue-600/20 px-3 py-1.5 text-xs text-blue-400 hover:bg-blue-600/40 transition"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => openDeleteModal(department)}
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
            <div className="px-8 py-6 border-b border-white/10 flex items-center justify-between">
              <h2 className="text-2xl font-semibold">Create Department</h2>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-white transition text-2xl">&times;</button>
            </div>
            <div className="px-8 py-6 space-y-6">
              {formError && (
                <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-red-400 text-sm">{formError}</div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm text-slate-300 mb-1">Name *</label>
                  <input
                    type="text"
                    value={createForm.name}
                    onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="Department name"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm text-slate-300 mb-1">Company ID *</label>
                  <input
                    type="number"
                    value={createForm.company_id || ''}
                    onChange={(e) => setCreateForm({ ...createForm, company_id: parseInt(e.target.value) || 0 })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="Company ID"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm text-slate-300 mb-1">Description</label>
                  <textarea
                    value={createForm.description || ''}
                    onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    rows={3}
                    placeholder="Department description"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Manager ID</label>
                  <input
                    type="number"
                    value={createForm.manager_id || ''}
                    onChange={(e) => setCreateForm({ ...createForm, manager_id: e.target.value ? parseInt(e.target.value) : undefined })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="Manager user ID"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Budget</label>
                  <input
                    type="text"
                    value={createForm.budget || ''}
                    onChange={(e) => setCreateForm({ ...createForm, budget: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="e.g., $100,000 or 100K"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm text-slate-300 mb-1">Location</label>
                  <input
                    type="text"
                    value={createForm.location || ''}
                    onChange={(e) => setCreateForm({ ...createForm, location: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="Department location"
                  />
                </div>
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
                disabled={submitting || !createForm.name || !createForm.company_id}
                className="rounded-xl bg-cyan-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-cyan-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Creating...' : 'Create Department'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedDepartment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
            <div className="px-8 py-6 border-b border-white/10 flex items-center justify-between">
              <h2 className="text-2xl font-semibold">Edit Department</h2>
              <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-white transition text-2xl">&times;</button>
            </div>
            <div className="px-8 py-6 space-y-6">
              {formError && (
                <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-red-400 text-sm">{formError}</div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm text-slate-300 mb-1">Name</label>
                  <input
                    type="text"
                    value={editForm.name || ''}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm text-slate-300 mb-1">Description</label>
                  <textarea
                    value={editForm.description || ''}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Manager ID</label>
                  <input
                    type="number"
                    value={editForm.manager_id || ''}
                    onChange={(e) => setEditForm({ ...editForm, manager_id: e.target.value ? parseInt(e.target.value) : undefined })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Budget</label>
                  <input
                    type="text"
                    value={editForm.budget || ''}
                    onChange={(e) => setEditForm({ ...editForm, budget: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm text-slate-300 mb-1">Location</label>
                  <input
                    type="text"
                    value={editForm.location || ''}
                    onChange={(e) => setEditForm({ ...editForm, location: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Status</label>
                  <select
                    value={editForm.is_active ? 'active' : 'inactive'}
                    onChange={(e) => setEditForm({ ...editForm, is_active: e.target.value === 'active' })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50"
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
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
      {showDeleteModal && selectedDepartment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-md m-4">
            <div className="px-8 py-6 border-b border-white/10">
              <h2 className="text-2xl font-semibold text-red-400">Delete Department</h2>
            </div>
            <div className="px-8 py-6">
              {formError && (
                <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-red-400 text-sm mb-4">{formError}</div>
              )}
              <p className="text-slate-300">
                Are you sure you want to delete <strong className="text-white">{selectedDepartment.name}</strong>?
              </p>
              <p className="text-slate-400 text-sm mt-2">This action cannot be undone. All data associated with this department may be affected.</p>
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
                {submitting ? 'Deleting...' : 'Delete Department'}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}