"use client"

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  getTenants,
  getTenantStats,
  getTenantDetail,
  getTenantUsers,
  assignUserToCompany,
  removeUserFromCompany,
  TenantStats,
  TenantDetail,
  TenantListResponse,
  TenantUserSummary,
} from '../../lib/api';

export default function TenantsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<TenantStats | null>(null);
  const [tenants, setTenants] = useState<TenantDetail[]>([]);
  const [totalTenants, setTotalTenants] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [selectedTenant, setSelectedTenant] = useState<TenantDetail | null>(null);
  const [tenantUsers, setTenantUsers] = useState<TenantUserSummary[]>([]);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignUserId, setAssignUserId] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('ai_bos_token');
    if (!stored) {
      router.push('/');
      return;
    }
    setToken(stored);
  }, [router]);

  useEffect(() => {
    if (token) {
      fetchTenants();
      fetchStats();
    }
  }, [token, page, search]);

  async function fetchStats() {
    try {
      const data = await getTenantStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch tenant stats:', err);
    }
  }

  async function fetchTenants() {
    setLoading(true);
    setError(null);
    try {
      const data = await getTenants({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
      });
      setTenants(data.items);
      setTotalTenants(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tenants');
    } finally {
      setLoading(false);
    }
  }

  async function viewTenantDetail(tenantId: number) {
    setActionLoading(true);
    try {
      const data = await getTenantDetail(tenantId);
      setSelectedTenant(data);
      const users = await getTenantUsers(tenantId);
      setTenantUsers(users);
      setShowDetailModal(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tenant details');
    } finally {
      setActionLoading(false);
    }
  }

  async function handleAssignUser() {
    const userId = parseInt(assignUserId);
    if (!selectedTenant || isNaN(userId)) {
      setActionMessage('Please enter a valid user ID');
      return;
    }
    setActionLoading(true);
    setActionMessage(null);
    try {
      const result = await assignUserToCompany({
        user_id: userId,
        company_id: selectedTenant.id,
      });
      setActionMessage(result.message);
      setAssignUserId('');
      // Refresh users
      const users = await getTenantUsers(selectedTenant.id);
      setTenantUsers(users);
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Failed to assign user');
    } finally {
      setActionLoading(false);
    }
  }

  async function handleRemoveUser(userId: number) {
    setActionLoading(true);
    setActionMessage(null);
    try {
      const result = await removeUserFromCompany(userId);
      setActionMessage(result.message);
      // Refresh users
      if (selectedTenant) {
        const users = await getTenantUsers(selectedTenant.id);
        setTenantUsers(users);
      }
      fetchTenants();
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Failed to remove user');
    } finally {
      setActionLoading(false);
    }
  }

  const totalPages = Math.ceil(totalTenants / pageSize);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-6">Tenant Management</h1>

      {/* Error message */}
      {error && (
        <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded mb-6">
          {error}
          <button onClick={() => setError(null)} className="float-right font-bold">&times;</button>
        </div>
      )}

      {/* Action message */}
      {actionMessage && (
        <div className="bg-blue-900/50 border border-blue-500 text-blue-200 px-4 py-3 rounded mb-6">
          {actionMessage}
          <button onClick={() => setActionMessage(null)} className="float-right font-bold">&times;</button>
        </div>
      )}

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400">Total Companies</div>
            <div className="text-2xl font-bold">{stats.total_companies}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400">Active Companies</div>
            <div className="text-2xl font-bold text-green-400">{stats.active_companies}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400">Total Users</div>
            <div className="text-2xl font-bold">{stats.total_users}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400">Active Users</div>
            <div className="text-2xl font-bold text-green-400">{stats.active_users}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400">Env Variables</div>
            <div className="text-2xl font-bold">{stats.total_environment_variables}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400">Storage</div>
            <div className="text-2xl font-bold">{stats.storage_used_estimate}</div>
          </div>
        </div>
      )}

      {/* Search bar */}
      <div className="flex items-center gap-4 mb-6">
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="Search tenants by name, domain, email, or industry..."
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={fetchTenants}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
        >
          Search
        </button>
      </div>

      {/* Loading state */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading tenants...</p>
        </div>
      ) : (
        <>
          {/* Tenants table */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-700 text-left">
                  <th className="px-4 py-3 text-sm font-medium text-gray-300">ID</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-300">Name</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-300">Domain</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-300">Industry</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-300">Users</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-300">Plan</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-300">Status</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-300">Actions</th>
                </tr>
              </thead>
              <tbody>
                {tenants.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                      No tenants found
                    </td>
                  </tr>
                ) : (
                  tenants.map((tenant) => (
                    <tr key={tenant.id} className="border-t border-gray-700 hover:bg-gray-750">
                      <td className="px-4 py-3 text-sm">{tenant.id}</td>
                      <td className="px-4 py-3 text-sm font-medium">{tenant.name}</td>
                      <td className="px-4 py-3 text-sm text-gray-400">{tenant.domain}</td>
                      <td className="px-4 py-3 text-sm text-gray-400">{tenant.industry || '-'}</td>
                      <td className="px-4 py-3 text-sm">{tenant.user_count}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 rounded text-xs ${
                          tenant.subscription_plan === 'enterprise'
                            ? 'bg-purple-900/50 text-purple-300'
                            : tenant.subscription_plan === 'professional'
                            ? 'bg-blue-900/50 text-blue-300'
                            : tenant.subscription_plan === 'starter'
                            ? 'bg-green-900/50 text-green-300'
                            : 'bg-gray-700 text-gray-300'
                        }`}>
                          {tenant.subscription_plan}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 rounded text-xs ${
                          tenant.is_active
                            ? 'bg-green-900/50 text-green-300'
                            : 'bg-red-900/50 text-red-300'
                        }`}>
                          {tenant.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <button
                          onClick={() => viewTenantDetail(tenant.id)}
                          className="text-blue-400 hover:text-blue-300 mr-3"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 mt-6">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page <= 1}
                className="px-4 py-2 bg-gray-800 rounded-lg border border-gray-700 disabled:opacity-50 hover:bg-gray-700 transition-colors"
              >
                Previous
              </button>
              <span className="text-gray-400">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page >= totalPages}
                className="px-4 py-2 bg-gray-800 rounded-lg border border-gray-700 disabled:opacity-50 hover:bg-gray-700 transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {/* Tenant Detail Modal */}
      {showDetailModal && selectedTenant && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg w-full max-w-2xl max-h-[80vh] overflow-y-auto border border-gray-700">
            <div className="flex items-center justify-between p-6 border-b border-gray-700">
              <h2 className="text-xl font-bold">{selectedTenant.name}</h2>
              <button
                onClick={() => { setShowDetailModal(false); setActionMessage(null); }}
                className="text-gray-400 hover:text-white text-2xl"
              >
                &times;
              </button>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="text-sm text-gray-400">Domain</label>
                  <p className="text-white">{selectedTenant.domain}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Industry</label>
                  <p className="text-white">{selectedTenant.industry || '-'}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Subscription Plan</label>
                  <p className="text-white">{selectedTenant.subscription_plan}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Status</label>
                  <p className={selectedTenant.is_active ? 'text-green-400' : 'text-red-400'}>
                    {selectedTenant.is_active ? 'Active' : 'Inactive'}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Employee Count</label>
                  <p className="text-white">{selectedTenant.employee_count || '-'}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Description</label>
                  <p className="text-white">{selectedTenant.description || '-'}</p>
                </div>
              </div>

              {/* Assign User */}
              <div className="border-t border-gray-700 pt-6 mb-6">
                <h3 className="text-lg font-semibold mb-4">Assign User to Company</h3>
                <div className="flex gap-4 items-end">
                  <div className="flex-1">
                    <label className="text-sm text-gray-400 block mb-1">User ID</label>
                    <input
                      type="number"
                      value={assignUserId}
                      onChange={(e) => setAssignUserId(e.target.value)}
                      placeholder="Enter user ID"
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <button
                    onClick={handleAssignUser}
                    disabled={actionLoading}
                    className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-4 py-2 rounded-lg transition-colors"
                  >
                    {actionLoading ? 'Assigning...' : 'Assign'}
                  </button>
                </div>
              </div>

              {/* Tenant Users */}
              <div className="border-t border-gray-700 pt-6">
                <h3 className="text-lg font-semibold mb-4">
                  Users ({tenantUsers.length})
                </h3>
                {tenantUsers.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No users assigned</p>
                ) : (
                  <div className="space-y-3">
                    {tenantUsers.map((user) => (
                      <div key={user.id} className="flex items-center justify-between bg-gray-700/50 rounded-lg p-3">
                        <div>
                          <p className="font-medium">{user.email}</p>
                          <p className="text-sm text-gray-400">
                            {user.full_name || user.username || 'No name'}
                            {user.is_superuser && (
                              <span className="ml-2 px-2 py-0.5 bg-purple-900/50 text-purple-300 rounded text-xs">Superuser</span>
                            )}
                          </p>
                        </div>
                        <button
                          onClick={() => handleRemoveUser(user.id)}
                          disabled={actionLoading}
                          className="text-red-400 hover:text-red-300 text-sm disabled:opacity-50"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}