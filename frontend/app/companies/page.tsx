"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../context/AuthContext'
import { 
  getCompanyList, getCompanyStats, createCompany, updateCompany, deleteCompany, 
  Company, CompanyCreate, CompanyUpdate, CompanyStats 
} from '../../lib/api'

export default function CompaniesPage() {
  const { isAuthenticated, logout } = useAuth()
  const router = useRouter()
  const [companies, setCompanies] = useState<Company[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<CompanyStats | null>(null)
  const [isSuperuser, setIsSuperuser] = useState(false)
  
  // Search & Filter state
  const [search, setSearch] = useState('')
  const [isActiveFilter, setIsActiveFilter] = useState<string>('all')
  const [industryFilter, setIndustryFilter] = useState('')
  const [planFilter, setPlanFilter] = useState('')
  const [sortBy, setSortBy] = useState('name')
  const [sortOrder, setSortOrder] = useState('asc')

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Create form
  const [createForm, setCreateForm] = useState<CompanyCreate>({
    name: '',
    domain: '',
    description: '',
    address: '',
    phone: '',
    email: '',
    website: '',
    tax_id: '',
    industry: '',
    employee_count: undefined,
    subscription_plan: 'free',
    subscription_status: 'active',
  })

  // Edit form
  const [editForm, setEditForm] = useState<CompanyUpdate>({})

  const fetchData = async () => {
    try {
      setLoading(true)
      const [listResponse, statsData] = await Promise.all([
        getCompanyList({
          skip: (page - 1) * pageSize,
          limit: pageSize,
          search: search || undefined,
          is_active: isActiveFilter === 'all' ? undefined : isActiveFilter === 'active',
          industry: industryFilter || undefined,
          subscription_plan: planFilter || undefined,
          sort_by: sortBy,
          sort_order: sortOrder,
        }),
        getCompanyStats(),
      ])
      setCompanies(listResponse.items)
      setTotal(listResponse.total)
      setStats(statsData)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load companies')
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
  }, [search, isActiveFilter, industryFilter, planFilter])

  const totalPages = Math.ceil(total / pageSize)

  const handleCreate = async () => {
    setFormError(null)
    setSubmitting(true)
    try {
      await createCompany(createForm)
      setShowCreateModal(false)
      setCreateForm({
        name: '',
        domain: '',
        description: '',
        address: '',
        phone: '',
        email: '',
        website: '',
        tax_id: '',
        industry: '',
        employee_count: undefined,
        subscription_plan: 'free',
        subscription_status: 'active',
      })
      fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create company')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = async () => {
    if (!selectedCompany) return
    setFormError(null)
    setSubmitting(true)
    try {
      await updateCompany(selectedCompany.id, editForm)
      setShowEditModal(false)
      setSelectedCompany(null)
      setEditForm({})
      fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update company')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedCompany) return
    setFormError(null)
    setSubmitting(true)
    try {
      await deleteCompany(selectedCompany.id)
      setShowDeleteModal(false)
      setSelectedCompany(null)
      fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to delete company')
    } finally {
      setSubmitting(false)
    }
  }

  const openEditModal = (company: Company) => {
    setSelectedCompany(company)
    setEditForm({
      name: company.name,
      domain: company.domain,
      description: company.description,
      address: company.address,
      phone: company.phone,
      email: company.email,
      website: company.website,
      logo_url: company.logo_url,
      tax_id: company.tax_id,
      industry: company.industry,
      employee_count: company.employee_count,
      is_active: company.is_active,
      subscription_plan: company.subscription_plan,
      subscription_status: company.subscription_status,
      subscription_expires_at: company.subscription_expires_at,
    })
    setFormError(null)
    setShowEditModal(true)
  }

  const openDeleteModal = (company: Company) => {
    setSelectedCompany(company)
    setFormError(null)
    setShowDeleteModal(true)
  }

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  if (loading && companies.length === 0) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="flex items-center justify-center h-64">
            <div className="text-cyan-400 text-xl animate-pulse">Loading companies...</div>
          </div>
        </div>
      </main>
    )
  }

  if (error && companies.length === 0) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
            <h2 className="text-2xl font-semibold text-red-400 mb-2">Error Loading Companies</h2>
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
            <h1 className="text-4xl font-semibold mt-2">Companies Management</h1>
            <p className="text-slate-400 mt-1">Manage tenant organizations and their subscriptions</p>
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
              <p className="text-slate-400 text-sm">Total Companies</p>
              <p className="text-3xl font-semibold text-white mt-1">{stats.total_companies}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-5">
              <p className="text-slate-400 text-sm">Active</p>
              <p className="text-3xl font-semibold text-green-400 mt-1">{stats.active_companies}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-5">
              <p className="text-slate-400 text-sm">Total Users</p>
              <p className="text-3xl font-semibold text-cyan-400 mt-1">{stats.total_users_across_companies}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-5">
              <p className="text-slate-400 text-sm">Avg Employees</p>
              <p className="text-3xl font-semibold text-purple-400 mt-1">
                {stats.avg_employees ? Math.round(stats.avg_employees) : '—'}
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
              placeholder="Search by name, domain, email..."
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
            <label className="block text-xs text-slate-400 mb-1">Plan</label>
            <select
              value={planFilter}
              onChange={(e) => setPlanFilter(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition"
            >
              <option value="">All Plans</option>
              <option value="free">Free</option>
              <option value="starter">Starter</option>
              <option value="professional">Professional</option>
              <option value="enterprise">Enterprise</option>
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
              <option value="domain">Domain</option>
              <option value="created_at">Created</option>
              <option value="employee_count">Employees</option>
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
              + Create Company
            </button>
          )}
          <button
            onClick={fetchData}
            className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
          >
            Refresh
          </button>
        </div>

        {/* Companies Table */}
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
          <div className="px-8 py-6 border-b border-white/10">
            <h2 className="text-2xl font-semibold">All Companies ({total})</h2>
          </div>
          
          {companies.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              No companies found. Create your first company to get started.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-900/50">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">ID</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Name</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Domain</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Industry</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Plan</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Users</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Status</th>
                    {isSuperuser && <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {companies.map((company) => (
                    <tr key={company.id} className="hover:bg-white/5 transition">
                      <td className="px-6 py-4 text-sm text-slate-400">{company.id}</td>
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-white font-medium">{company.name}</div>
                          {company.email && (
                            <div className="text-xs text-slate-400 mt-0.5">{company.email}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-300">{company.domain}</td>
                      <td className="px-6 py-4 text-sm text-slate-300">
                        {company.industry || <span className="text-slate-600">—</span>}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          company.subscription_plan === 'enterprise' 
                            ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30'
                            : company.subscription_plan === 'professional'
                            ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                            : company.subscription_plan === 'starter'
                            ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
                            : 'bg-slate-500/10 text-slate-400 border border-slate-500/30'
                        }`}>
                          {company.subscription_plan || 'free'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-300">
                        {company.user_count !== undefined ? company.user_count : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                          company.is_active
                            ? 'bg-green-500/10 text-green-400 border border-green-500/30'
                            : 'bg-red-500/10 text-red-400 border border-red-500/30'
                        }`}>
                          {company.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      {isSuperuser && (
                        <td className="px-6 py-4">
                          <div className="flex gap-2">
                            <button
                              onClick={() => openEditModal(company)}
                              className="rounded-lg bg-blue-600/20 px-3 py-1.5 text-xs text-blue-400 hover:bg-blue-600/40 transition"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => openDeleteModal(company)}
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
              <h2 className="text-2xl font-semibold">Create Company</h2>
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
                    placeholder="Company name"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm text-slate-300 mb-1">Domain *</label>
                  <input
                    type="text"
                    value={createForm.domain}
                    onChange={(e) => setCreateForm({ ...createForm, domain: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="company-domain.com"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm text-slate-300 mb-1">Description</label>
                  <textarea
                    value={createForm.description || ''}
                    onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    rows={3}
                    placeholder="Company description"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Email</label>
                  <input
                    type="email"
                    value={createForm.email || ''}
                    onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="info@company.com"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Phone</label>
                  <input
                    type="text"
                    value={createForm.phone || ''}
                    onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Website</label>
                  <input
                    type="text"
                    value={createForm.website || ''}
                    onChange={(e) => setCreateForm({ ...createForm, website: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="https://company.com"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Industry</label>
                  <input
                    type="text"
                    value={createForm.industry || ''}
                    onChange={(e) => setCreateForm({ ...createForm, industry: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="Technology"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Tax ID</label>
                  <input
                    type="text"
                    value={createForm.tax_id || ''}
                    onChange={(e) => setCreateForm({ ...createForm, tax_id: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="Tax ID / VAT"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Employees</label>
                  <input
                    type="number"
                    value={createForm.employee_count ?? ''}
                    onChange={(e) => setCreateForm({ ...createForm, employee_count: e.target.value ? parseInt(e.target.value) : undefined })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="Number of employees"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Address</label>
                  <input
                    type="text"
                    value={createForm.address || ''}
                    onChange={(e) => setCreateForm({ ...createForm, address: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    placeholder="Company address"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Subscription Plan</label>
                  <select
                    value={createForm.subscription_plan || 'free'}
                    onChange={(e) => setCreateForm({ ...createForm, subscription_plan: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50"
                  >
                    <option value="free">Free</option>
                    <option value="starter">Starter</option>
                    <option value="professional">Professional</option>
                    <option value="enterprise">Enterprise</option>
                    <option value="custom">Custom</option>
                  </select>
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
                disabled={submitting || !createForm.name || !createForm.domain}
                className="rounded-xl bg-cyan-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-cyan-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Creating...' : 'Create Company'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedCompany && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
            <div className="px-8 py-6 border-b border-white/10 flex items-center justify-between">
              <h2 className="text-2xl font-semibold">Edit Company</h2>
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
                  <label className="block text-sm text-slate-300 mb-1">Domain</label>
                  <input
                    type="text"
                    value={editForm.domain || ''}
                    onChange={(e) => setEditForm({ ...editForm, domain: e.target.value })}
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
                  <label className="block text-sm text-slate-300 mb-1">Email</label>
                  <input
                    type="email"
                    value={editForm.email || ''}
                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Phone</label>
                  <input
                    type="text"
                    value={editForm.phone || ''}
                    onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Website</label>
                  <input
                    type="text"
                    value={editForm.website || ''}
                    onChange={(e) => setEditForm({ ...editForm, website: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Industry</label>
                  <input
                    type="text"
                    value={editForm.industry || ''}
                    onChange={(e) => setEditForm({ ...editForm, industry: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Employees</label>
                  <input
                    type="number"
                    value={editForm.employee_count ?? ''}
                    onChange={(e) => setEditForm({ ...editForm, employee_count: e.target.value ? parseInt(e.target.value) : undefined })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Subscription Plan</label>
                  <select
                    value={editForm.subscription_plan || 'free'}
                    onChange={(e) => setEditForm({ ...editForm, subscription_plan: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50"
                  >
                    <option value="free">Free</option>
                    <option value="starter">Starter</option>
                    <option value="professional">Professional</option>
                    <option value="enterprise">Enterprise</option>
                    <option value="custom">Custom</option>
                  </select>
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
      {showDeleteModal && selectedCompany && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-md m-4">
            <div className="px-8 py-6 border-b border-white/10">
              <h2 className="text-2xl font-semibold text-red-400">Delete Company</h2>
            </div>
            <div className="px-8 py-6">
              {formError && (
                <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-red-400 text-sm mb-4">{formError}</div>
              )}
              <p className="text-slate-300">
                Are you sure you want to delete <strong className="text-white">{selectedCompany.name}</strong>?
              </p>
              <p className="text-slate-400 text-sm mt-2">This action cannot be undone. All data associated with this company may be affected.</p>
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
                {submitting ? 'Deleting...' : 'Delete Company'}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}