"use client"

import { useState, useEffect } from "react"
import { useAuth } from "../../context/AuthContext"
import { useRouter } from "next/navigation"
import { getAuditLogs, getMyAuditLogs, AuditLog } from "../../lib/api"

export default function AuditLogsPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuth()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionFilter, setActionFilter] = useState<string>("")
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string>("")
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/")
      return
    }
  }, [isAuthenticated, router])

  const fetchLogs = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await getMyAuditLogs({
        skip: (page - 1) * 50,
        limit: 50,
        action: actionFilter || undefined,
        resource_type: resourceTypeFilter || undefined,
      })
      setLogs(response.items)
      setTotal(response.total)
    } catch (err: any) {
      setError(err.message || "Failed to fetch audit logs")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      fetchLogs()
    }
  }, [isAuthenticated, page, actionFilter, resourceTypeFilter])

  const handleFilterChange = () => {
    setPage(1)
    fetchLogs()
  }

  const clearFilters = () => {
    setActionFilter("")
    setResourceTypeFilter("")
    setPage(1)
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">Audit Logs</h1>
          <button
            onClick={fetchLogs}
            className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
          >
            Refresh
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-xl bg-red-900/20 border border-red-800 p-4 text-red-300">
            {error}
          </div>
        )}

        <div className="mb-6 rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Action</label>
              <input
                type="text"
                value={actionFilter}
                onChange={(e) => setActionFilter(e.target.value)}
                placeholder="Filter by action..."
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Resource Type</label>
              <input
                type="text"
                value={resourceTypeFilter}
                onChange={(e) => setResourceTypeFilter(e.target.value)}
                placeholder="Filter by resource type..."
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div className="flex items-end gap-2">
              <button
                onClick={handleFilterChange}
                className="rounded-xl border border-cyan-700 bg-cyan-900/30 px-4 py-2 text-sm text-cyan-300 hover:bg-cyan-900/50 transition"
              >
                Apply Filters
              </button>
              <button
                onClick={clearFilters}
                className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-400 hover:bg-slate-700 transition"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-400">Loading audit logs...</div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12 text-slate-400">No audit logs found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Action</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Resource Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Resource ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">IP Address</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Date</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-sm text-slate-300">{log.id}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-cyan-900/30 text-cyan-300">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">{log.resource_type}</td>
                    <td className="px-4 py-3 text-sm text-slate-400">{log.resource_id || "-"}</td>
                    <td className="px-4 py-3 text-sm text-slate-400">{log.ip_address || "-"}</td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {total > 50 && (
          <div className="mt-6 flex justify-between items-center">
            <span className="text-sm text-slate-400">
              Showing {(page - 1) * 50 + 1} - {Math.min(page * 50, total)} of {total} entries
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50 transition"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page * 50 >= total}
                className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50 transition"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
