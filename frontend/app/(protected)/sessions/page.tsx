"use client"

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../../context/AuthContext'
import { useRouter } from 'next/navigation'
import { 
  getSessions, 
  getSessionStats,
  terminateSession, 
  terminateAllSessions, 
  cleanupSessions,
  SessionInfo,
  SessionListResponse,
  SessionStats 
} from '../../../lib/api'

export default function SessionsPage() {
  const { isAuthenticated, token } = useAuth()
  const router = useRouter()
  const [sessions, setSessions] = useState<SessionInfo[]>([])
  const [stats, setStats] = useState<SessionStats | null>(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const [showTerminateAllConfirm, setShowTerminateAllConfirm] = useState(false)
  const [terminatingId, setTerminatingId] = useState<number | null>(null)

  const fetchSessions = useCallback(async () => {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      const [sessionsData, statsData] = await Promise.all([
        getSessions((page - 1) * pageSize, pageSize, includeInactive),
        getSessionStats()
      ])
      setSessions(sessionsData.items)
      setTotal(sessionsData.total)
      setStats(statsData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sessions')
    } finally {
      setLoading(false)
    }
  }, [token, page, pageSize, includeInactive])

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }
    fetchSessions()
  }, [isAuthenticated, router, fetchSessions])

  const handleTerminate = async (sessionId: number) => {
    setTerminatingId(sessionId)
    setError('')
    setSuccess('')
    try {
      await terminateSession(sessionId)
      setSuccess('Session terminated successfully')
      fetchSessions()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to terminate session')
    } finally {
      setTerminatingId(null)
    }
  }

  const handleTerminateAll = async () => {
    setError('')
    setSuccess('')
    try {
      const data = await terminateAllSessions()
      setSuccess(data.message || 'All sessions terminated successfully')
      setShowTerminateAllConfirm(false)
      fetchSessions()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to terminate all sessions')
    }
  }

  const handleCleanup = async () => {
    setError('')
    setSuccess('')
    try {
      const data = await cleanupSessions()
      setSuccess(data.message || 'Expired sessions cleaned up')
      fetchSessions()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cleanup sessions')
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleString()
  }

  const isExpired = (expiresAt: string) => {
    return new Date(expiresAt) < new Date()
  }

  const getStatusBadge = (session: SessionInfo) => {
    if (!session.is_active) {
      return <span className="rounded-full bg-gray-500/10 px-2.5 py-0.5 text-xs text-gray-400">Terminated</span>
    }
    if (isExpired(session.expires_at)) {
      return <span className="rounded-full bg-yellow-500/10 px-2.5 py-0.5 text-xs text-yellow-400">Expired</span>
    }
    return <span className="rounded-full bg-green-500/10 px-2.5 py-0.5 text-xs text-green-400">Active</span>
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-white">Session Management</h1>
            <p className="mt-2 text-slate-400">Monitor and manage your active sessions across devices</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleCleanup}
              className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
            >
              Cleanup Expired
            </button>
            <button
              onClick={() => setShowTerminateAllConfirm(true)}
              className="rounded-xl border border-red-700 bg-red-900/50 px-4 py-2 text-sm text-red-300 hover:bg-red-800 hover:text-red-200 transition"
            >
              Terminate All
            </button>
          </div>
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

        {stats && (
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-white/10 bg-slate-900/50 p-4">
              <p className="text-sm text-slate-400">Total Sessions</p>
              <p className="mt-1 text-2xl font-semibold text-white">{stats.total_sessions}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-slate-900/50 p-4">
              <p className="text-sm text-slate-400">Active</p>
              <p className="mt-1 text-2xl font-semibold text-green-400">{stats.active_sessions}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-slate-900/50 p-4">
              <p className="text-sm text-slate-400">Inactive</p>
              <p className="mt-1 text-2xl font-semibold text-gray-400">{stats.inactive_sessions}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-slate-900/50 p-4">
              <p className="text-sm text-slate-400">Expired</p>
              <p className="mt-1 text-2xl font-semibold text-yellow-400">{stats.expired_sessions}</p>
            </div>
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
            Include inactive sessions
          </label>
          <span className="text-sm text-slate-500">
            {total} session{total !== 1 ? 's' : ''} found
          </span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-12 text-center">
            <p className="text-slate-400">No sessions found</p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-white/10">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 bg-slate-900/80">
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">ID</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Device</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Browser/OS</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Status</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">IP Address</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Last Activity</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Expires</th>
                  <th className="px-4 py-3 text-right text-slate-400 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => {
                  const expired = isExpired(s.expires_at)
                  const terminated = !s.is_active
                  return (
                    <tr key={s.id} className="border-b border-white/5 hover:bg-white/5 transition">
                      <td className="px-4 py-3 text-slate-300">{s.id}</td>
                      <td className="px-4 py-3">
                        <div>
                          <p className="text-slate-300">{s.device_name || 'Unknown Device'}</p>
                          <p className="text-xs text-slate-500">{s.device_type || 'unknown'}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div>
                          <p className="text-slate-300">{s.browser || 'Unknown'}</p>
                          <p className="text-xs text-slate-500">{s.os || 'Unknown'}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {getStatusBadge(s)}
                      </td>
                      <td className="px-4 py-3 text-slate-400 font-mono text-xs">{s.ip_address || 'N/A'}</td>
                      <td className="px-4 py-3 text-slate-400">{formatDate(s.last_activity_at)}</td>
                      <td className={`px-4 py-3 ${expired ? 'text-yellow-400' : 'text-slate-400'}`}>
                        {formatDate(s.expires_at)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {!terminated && !expired && (
                          <button
                            onClick={() => handleTerminate(s.id)}
                            disabled={terminatingId === s.id}
                            className="rounded-lg bg-red-500/10 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/20 transition disabled:opacity-50"
                          >
                            {terminatingId === s.id ? 'Terminating...' : 'Terminate'}
                          </button>
                        )}
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

        {showTerminateAllConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
              <h3 className="text-lg font-semibold text-white">Terminate All Sessions</h3>
              <p className="mt-2 text-sm text-slate-400">
                This will terminate all your active sessions. You will need to log in again on all devices.
              </p>
              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={() => setShowTerminateAllConfirm(false)}
                  className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleTerminateAll}
                  className="rounded-xl bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-500 transition"
                >
                  Terminate All
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}