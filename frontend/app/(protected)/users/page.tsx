"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../context/AuthContext'
import { getUsers, createUser, updateUser, deleteUser, User } from '../../../lib/api'

export default function UsersPage() {
  const { isAuthenticated, logout } = useAuth()
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    username: '',
    password: '',
    is_active: true,
    is_superuser: false,
  })
  const [formError, setFormError] = useState<string | null>(null)
  const [formLoading, setFormLoading] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }
    fetchUsers()
  }, [isAuthenticated, router])

  async function fetchUsers() {
    try {
      setLoading(true)
      const data = await getUsers()
      setUsers(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  const resetForm = () => {
    setFormData({
      email: '',
      full_name: '',
      username: '',
      password: '',
      is_active: true,
      is_superuser: false,
    })
    setFormError(null)
  }

  const handleCreate = async () => {
    setFormLoading(true)
    setFormError(null)
    try {
      await createUser({
        email: formData.email,
        full_name: formData.full_name || undefined,
        username: formData.username || undefined,
        password: formData.password,
      })
      setShowCreateModal(false)
      resetForm()
      await fetchUsers()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create user')
    } finally {
      setFormLoading(false)
    }
  }

  const handleEdit = async () => {
    if (!selectedUser) return
    setFormLoading(true)
    setFormError(null)
    try {
      await updateUser(selectedUser.id, {
        email: formData.email || undefined,
        full_name: formData.full_name || undefined,
        username: formData.username || undefined,
        ...(formData.password ? { password: formData.password } : {}),
        is_active: formData.is_active,
        is_superuser: formData.is_superuser,
      })
      setShowEditModal(false)
      setSelectedUser(null)
      resetForm()
      await fetchUsers()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update user')
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedUser) return
    setFormLoading(true)
    setFormError(null)
    try {
      await deleteUser(selectedUser.id)
      setShowDeleteModal(false)
      setSelectedUser(null)
      await fetchUsers()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to delete user')
    } finally {
      setFormLoading(false)
    }
  }

  const openEditModal = (user: User) => {
    setSelectedUser(user)
    setFormData({
      email: user.email,
      full_name: user.full_name || '',
      username: '',
      password: '',
      is_active: user.is_active,
      is_superuser: user.is_superuser,
    })
    setFormError(null)
    setShowEditModal(true)
  }

  const openDeleteModal = (user: User) => {
    setSelectedUser(user)
    setFormError(null)
    setShowDeleteModal(true)
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="flex items-center justify-center h-64">
            <div className="text-cyan-400 text-xl animate-pulse">Loading users...</div>
          </div>
        </div>
      </main>
    )
  }

  if (error) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
            <h2 className="text-2xl font-semibold text-red-400 mb-2">Error Loading Users</h2>
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
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="text-4xl font-semibold mt-2">Users Management</h1>
            <p className="text-slate-400 mt-1">Manage platform users and collaborators</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowCreateModal(true)}
              className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 transition"
            >
              + Create User
            </button>
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

        {/* Users Table */}
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
          <div className="px-8 py-6 border-b border-white/10 flex items-center justify-between">
            <h2 className="text-2xl font-semibold">All Users ({users.length})</h2>
            <button onClick={fetchUsers} className="text-sm text-slate-400 hover:text-white transition">
              Refresh
            </button>
          </div>
          
          {users.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              No users found. Create your first user to get started.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-900/50">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">ID</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Email</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Full Name</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Status</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Role</th>
                    <th className="px-6 py-4 text-right text-sm font-medium text-slate-300">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-white/5 transition">
                      <td className="px-6 py-4 text-sm text-white">{user.id}</td>
                      <td className="px-6 py-4 text-sm text-white">{user.email}</td>
                      <td className="px-6 py-4 text-sm text-slate-300">{user.full_name || '-'}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                          user.is_active
                            ? 'bg-green-500/10 text-green-400 border border-green-500/30'
                            : 'bg-red-500/10 text-red-400 border border-red-500/30'
                        }`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                          user.is_superuser
                            ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30'
                            : 'bg-slate-500/10 text-slate-400 border border-slate-500/30'
                        }`}>
                          {user.is_superuser ? 'Admin' : 'User'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => openEditModal(user)}
                          className="text-sm text-cyan-400 hover:text-cyan-300 mr-4 transition"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => openDeleteModal(user)}
                          className="text-sm text-red-400 hover:text-red-300 transition"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-2xl">
            <h3 className="text-2xl font-semibold mb-6">Create New User</h3>
            
            {formError && (
              <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400">
                {formError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1">Email *</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="user@example.com"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Username</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="johndoe"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Password *</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="Min 8 characters"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-8">
              <button
                onClick={() => { setShowCreateModal(false); resetForm() }}
                className="rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={formLoading || !formData.email || !formData.password}
                className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {formLoading ? 'Creating...' : 'Create User'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-2xl">
            <h3 className="text-2xl font-semibold mb-6">Edit User: {selectedUser.email}</h3>
            
            {formError && (
              <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400">
                {formError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Username</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">New Password (leave blank to keep current)</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="Min 8 characters"
                />
              </div>
              <div className="flex gap-6">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="rounded bg-slate-800 border-slate-600 text-cyan-500 focus:ring-cyan-500"
                  />
                  <span className="text-sm text-slate-300">Active</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_superuser}
                    onChange={(e) => setFormData({ ...formData, is_superuser: e.target.checked })}
                    className="rounded bg-slate-800 border-slate-600 text-cyan-500 focus:ring-cyan-500"
                  />
                  <span className="text-sm text-slate-300">Superuser</span>
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-8">
              <button
                onClick={() => { setShowEditModal(false); setSelectedUser(null); resetForm() }}
                className="rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleEdit}
                disabled={formLoading}
                className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {formLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-2xl text-center">
            <h3 className="text-2xl font-semibold mb-2">Delete User</h3>
            <p className="text-slate-400 mb-2">
              Are you sure you want to delete this user?
            </p>
            <p className="text-lg font-medium text-white mb-6">
              {selectedUser.email}
            </p>

            {formError && (
              <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400">
                {formError}
              </div>
            )}

            <div className="flex justify-center gap-3">
              <button
                onClick={() => { setShowDeleteModal(false); setSelectedUser(null); resetForm() }}
                className="rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={formLoading}
                className="rounded-xl bg-red-600 px-5 py-2.5 text-sm text-white hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {formLoading ? 'Deleting...' : 'Delete User'}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}