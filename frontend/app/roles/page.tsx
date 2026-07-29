"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../context/AuthContext'
import {
  getPermissions,
  getRoles,
  getRole,
  createRole,
  updateRole,
  deleteRole,
  assignRoleToUser,
  removeRoleFromUser,
  getRoleUsers,
  Permission,
  Role,
  RoleList,
  UserWithRoles,
} from '../../lib/api'

export default function RolesPage() {
  const { isAuthenticated, logout } = useAuth()
  const router = useRouter()
  const [roles, setRoles] = useState<RoleList[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [roleUsers, setRoleUsers] = useState<UserWithRoles[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permission_ids: [] as number[],
  })
  const [formError, setFormError] = useState<string | null>(null)
  const [formLoading, setFormLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'roles' | 'permissions'>('roles')

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }
    fetchData()
  }, [isAuthenticated, router])

  async function fetchData() {
    try {
      setLoading(true)
      const [rolesData, permissionsData] = await Promise.all([
        getRoles(),
        getPermissions(),
      ])
      setRoles(rolesData)
      setPermissions(permissionsData)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
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
      name: '',
      description: '',
      permission_ids: [],
    })
    setFormError(null)
  }

  const handleCreate = async () => {
    setFormLoading(true)
    setFormError(null)
    try {
      await createRole({
        name: formData.name,
        description: formData.description || undefined,
        permission_ids: formData.permission_ids,
      })
      setShowCreateModal(false)
      resetForm()
      await fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create role')
    } finally {
      setFormLoading(false)
    }
  }

  const handleEdit = async () => {
    if (!selectedRole) return
    setFormLoading(true)
    setFormError(null)
    try {
      await updateRole(selectedRole.id, {
        name: formData.name,
        description: formData.description || undefined,
        permission_ids: formData.permission_ids,
      })
      setShowEditModal(false)
      setSelectedRole(null)
      resetForm()
      await fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update role')
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedRole) return
    setFormLoading(true)
    setFormError(null)
    try {
      await deleteRole(selectedRole.id)
      setShowDeleteModal(false)
      setSelectedRole(null)
      await fetchData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to delete role')
    } finally {
      setFormLoading(false)
    }
  }

  const openEditModal = async (role: RoleList) => {
    setSelectedRole(null)
    try {
      const fullRole = await getRole(role.id)
      setSelectedRole(fullRole)
      setFormData({
        name: fullRole.name,
        description: fullRole.description || '',
        permission_ids: fullRole.permissions.map(p => p.id),
      })
      setFormError(null)
      setShowEditModal(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load role details')
    }
  }

  const openDeleteModal = (role: RoleList) => {
    setSelectedRole(null)
    setFormError(null)
    setShowDeleteModal(true)
    // Store minimal role info for deletion
    setSelectedRole({ id: role.id, name: role.name, is_system_role: role.is_system_role, created_at: role.created_at, permissions: [] } as Role)
  }

  const openAssignModal = async (role: RoleList) => {
  console.log("Opening role:", role.id);

  try {
    console.log("Calling getRoleUsers...");
    const roleUsersData = await getRoleUsers(role.id);
    console.log("Role users:", JSON.stringify(roleUsersData, null, 2));

    console.log("Calling getUsers...");
    const allUsers = await getUsers();
    console.log("All users:", JSON.stringify(allUsers, null, 2));

    setRoleUsers(roleUsersData);
    setUsers(allUsers);

    setSelectedRole({
      id: role.id,
      name: role.name,
      is_system_role: role.is_system_role,
      created_at: role.created_at,
      permissions: [],
    } as Role);

    setShowAssignModal(true);
  } catch (err) {
    console.error(err);
    setError(err instanceof Error ? err.message : "Failed");
  }
};

  const handleAssignRole = async (userId: number) => {
    if (!selectedRole) return
    try {
      await assignRoleToUser(userId, selectedRole.id)
      // Refresh role users
      const updatedUsers = await getRoleUsers(selectedRole.id)
      setRoleUsers(updatedUsers)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to assign role')
    }
  }

  const handleRemoveRole = async (userId: number) => {
    if (!selectedRole) return
    try {
      await removeRoleFromUser(userId, selectedRole.id)
      // Refresh role users
      const updatedUsers = await getRoleUsers(selectedRole.id)
      setRoleUsers(updatedUsers)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to remove role')
    }
  }

  // Helper to get users not assigned to this role
  const getUnassignedUsers = () => {
    if (!selectedRole) return []
    const assignedUserIds = new Set(roleUsers.map(u => u.id))
    return users.filter(u => !assignedUserIds.has(u.id))
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="flex items-center justify-center h-64">
            <div className="text-cyan-400 text-xl animate-pulse">Loading roles and permissions...</div>
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
            <h2 className="text-2xl font-semibold text-red-400 mb-2">Error Loading Data</h2>
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
            <h1 className="text-4xl font-semibold mt-2">Roles & Permissions</h1>
            <p className="text-slate-400 mt-1">Manage roles, permissions, and access control</p>
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

        {/* Tabs */}
        <div className="flex gap-4 border-b border-white/10">
          <button
            onClick={() => setActiveTab('roles')}
            className={`pb-3 px-4 text-sm font-medium transition ${
              activeTab === 'roles'
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Roles ({roles.length})
          </button>
          <button
            onClick={() => setActiveTab('permissions')}
            className={`pb-3 px-4 text-sm font-medium transition ${
              activeTab === 'permissions'
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Permissions ({permissions.length})
          </button>
        </div>

        {/* Roles Tab */}
        {activeTab === 'roles' && (
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
            <div className="px-8 py-6 border-b border-white/10 flex items-center justify-between">
              <h2 className="text-2xl font-semibold">All Roles</h2>
              <button
                onClick={() => setShowCreateModal(true)}
                className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 transition"
              >
                + Create Role
              </button>
            </div>

            {roles.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                No roles found. Create your first role to get started.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-900/50">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Name</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Description</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Type</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Permissions</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Users</th>
                      <th className="px-6 py-4 text-right text-sm font-medium text-slate-300">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10">
                    {roles.map((role) => (
                      <tr key={role.id} className="hover:bg-white/5 transition">
                        <td className="px-6 py-4 text-sm text-white font-medium">{role.name}</td>
                        <td className="px-6 py-4 text-sm text-slate-300">{role.description || '-'}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                            role.is_system_role
                              ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30'
                              : 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                          }`}>
                            {role.is_system_role ? 'System' : 'Custom'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-300">{role.permission_count}</td>
                        <td className="px-6 py-4 text-sm text-slate-300">{role.user_count}</td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => openAssignModal(role)}
                            className="text-sm text-cyan-400 hover:text-cyan-300 mr-4 transition"
                          >
                            Assign
                          </button>
                          <button
                            onClick={() => openEditModal(role)}
                            className="text-sm text-cyan-400 hover:text-cyan-300 mr-4 transition"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => openDeleteModal(role)}
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
        )}

        {/* Permissions Tab */}
        {activeTab === 'permissions' && (
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
            <div className="px-8 py-6 border-b border-white/10">
              <h2 className="text-2xl font-semibold">All Permissions</h2>
              <p className="text-slate-400 text-sm mt-1">System permissions cannot be modified</p>
            </div>

            {permissions.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                No permissions found.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-900/50">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Name</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Resource</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Action</th>
                      <th className="px-6 py-4 text-left text-sm font-medium text-slate-300">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10">
                    {permissions.map((permission) => (
                      <tr key={permission.id} className="hover:bg-white/5 transition">
                        <td className="px-6 py-4 text-sm text-white font-medium">{permission.name}</td>
                        <td className="px-6 py-4 text-sm text-slate-300">{permission.resource}</td>
                        <td className="px-6 py-4">
                          <span className="inline-flex rounded-full px-3 py-1 text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                            {permission.action}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-300">{permission.description || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-2xl">
            <h3 className="text-2xl font-semibold mb-6">Create New Role</h3>

            {formError && (
              <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400">
                {formError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1">Role Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="e.g., editor, viewer, manager"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  placeholder="Describe this role's purpose"
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-2">Permissions</label>
                <div className="max-h-64 overflow-y-auto rounded-xl bg-slate-800 border border-slate-700 p-4 space-y-2">
                  {permissions.map((permission: Permission) => (
                    <label key={permission.id} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.permission_ids.includes(permission.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({
                              ...formData,
                              permission_ids: [...formData.permission_ids, permission.id],
                            })
                          } else {
                            setFormData({
                              ...formData,
                              permission_ids: formData.permission_ids.filter(id => id !== permission.id),
                            })
                          }
                        }}
                        className="rounded bg-slate-800 border-slate-600 text-cyan-500 focus:ring-cyan-500"
                      />
                      <span className="text-sm text-slate-300">
                        {permission.name} <span className="text-slate-500">({permission.resource}:{permission.action})</span>
                      </span>
                    </label>
                  ))}
                </div>
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
                disabled={formLoading || !formData.name}
                className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {formLoading ? 'Creating...' : 'Create Role'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedRole && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-2xl">
            <h3 className="text-2xl font-semibold mb-6">Edit Role: {selectedRole.name}</h3>

            {formError && (
              <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400">
                {formError}
              </div>
            )}

            {selectedRole.is_system_role && (
              <div className="mb-4 rounded-xl bg-yellow-500/10 border border-yellow-500/30 p-4 text-sm text-yellow-400">
                System roles cannot be renamed or deleted, but permissions can be modified.
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1">Role Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  disabled={selectedRole.is_system_role}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-2">Permissions</label>
                <div className="max-h-64 overflow-y-auto rounded-xl bg-slate-800 border border-slate-700 p-4 space-y-2">
                  {permissions.map((permission: Permission) => (
                    <label key={permission.id} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.permission_ids.includes(permission.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({
                              ...formData,
                              permission_ids: [...formData.permission_ids, permission.id],
                            })
                          } else {
                            setFormData({
                              ...formData,
                              permission_ids: formData.permission_ids.filter(id => id !== permission.id),
                            })
                          }
                        }}
                        className="rounded bg-slate-800 border-slate-600 text-cyan-500 focus:ring-cyan-500"
                      />
                      <span className="text-sm text-slate-300">
                        {permission.name} <span className="text-slate-500">({permission.resource}:{permission.action})</span>
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-8">
              <button
                onClick={() => { setShowEditModal(false); setSelectedRole(null); resetForm() }}
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
      {showDeleteModal && selectedRole && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-2xl text-center">
            <h3 className="text-2xl font-semibold mb-2">Delete Role</h3>
            <p className="text-slate-400 mb-2">
              Are you sure you want to delete this role?
            </p>
            <p className="text-lg font-medium text-white mb-6">
              {selectedRole.name}
            </p>

            {selectedRole.is_system_role && (
              <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400">
                System roles cannot be deleted.
              </div>
            )}

            {formError && (
              <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400">
                {formError}
              </div>
            )}

            <div className="flex justify-center gap-3">
              <button
                onClick={() => { setShowDeleteModal(false); setSelectedRole(null) }}
                className="rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={formLoading || selectedRole.is_system_role}
                className="rounded-xl bg-red-600 px-5 py-2.5 text-sm text-white hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {formLoading ? 'Deleting...' : 'Delete Role'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Assign Role Modal */}
      {showAssignModal && selectedRole && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-2xl">
            <h3 className="text-2xl font-semibold mb-2">Manage Users: {selectedRole.name}</h3>
            <p className="text-slate-400 text-sm mb-6">Assign or remove users from this role</p>

            {formError && (
              <div className="mb-4 rounded-xl bg-red-500/10 border border-red-500/30 p-4 text-sm text-red-400">
                {formError}
              </div>
            )}

            <div className="grid grid-cols-2 gap-6">
              {/* Assigned Users */}
              <div>
                <h4 className="text-sm font-medium text-slate-300 mb-3">
                  Assigned Users ({roleUsers.length})
                </h4>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {roleUsers.length === 0 ? (
                    <p className="text-sm text-slate-500 italic">No users assigned</p>
                  ) : (
                    roleUsers.map((user) => (
                      <div
                        key={user.id}
                        className="flex items-center justify-between rounded-xl bg-slate-800 border border-slate-700 px-4 py-3"
                      >
                        <div>
                          <p className="text-sm text-white">{user.email}</p>
                          <p className="text-xs text-slate-400">{user.full_name || user.username || 'No name'}</p>
                        </div>
                        <button
                          onClick={() => handleRemoveRole(user.id)}
                          className="text-xs text-red-400 hover:text-red-300 transition"
                        >
                          Remove
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Unassigned Users */}
              <div>
                <h4 className="text-sm font-medium text-slate-300 mb-3">
                  Available Users ({getUnassignedUsers().length})
                </h4>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {getUnassignedUsers().length === 0 ? (
                    <p className="text-sm text-slate-500 italic">All users assigned</p>
                  ) : (
                    getUnassignedUsers().map((user) => (
                      <div
                        key={user.id}
                        className="flex items-center justify-between rounded-xl bg-slate-800 border border-slate-700 px-4 py-3"
                      >
                        <div>
                          <p className="text-sm text-white">{user.email}</p>
                          <p className="text-xs text-slate-400">{user.full_name || user.username || 'No name'}</p>
                        </div>
                        <button
                          onClick={() => handleAssignRole(user.id)}
                          className="text-xs text-cyan-400 hover:text-cyan-300 transition"
                        >
                          Assign
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-8">
              <button
                onClick={() => { setShowAssignModal(false); setSelectedRole(null) }}
                className="rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}

// Helper function to get all users (not in api.ts by default)
async function getUsers(): Promise<User[]> {
  const response = await fetch('http://localhost:8000/api/v1/users/', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('ai_bos_token')}`,
    },
  })
  if (!response.ok) {
    throw new Error('Failed to fetch users')
  }
  return response.json()
}

interface User {
  id: number
  email: string
  full_name?: string
  username?: string
  is_active: boolean
  is_superuser: boolean
}