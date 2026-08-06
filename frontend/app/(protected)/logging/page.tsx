'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../context/AuthContext'
import {
  getLogEntries,
  getLogStats,
  cleanupLogs,
  LogEntry,
  LogStats,
} from '../../../lib/api'

const LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

export default function LoggingPage() {
  const router = useRouter()
  const { isAuthenticated, user } = useAuth()

  const [logs, setLogs] = useState<LogEntry[]>([])
  const [stats, setStats] = useState<LogStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [levelFilter, setLevelFilter] = useState<string>('')
  const [loggerFilter, setLoggerFilter] = useState<string>('')
  const [searchFilter, setSearchFilter] = useState<string>('')
  const [showFilters, setShowFilters] = useState(false)
  const [cleanupDays, setCleanupDays] = useState<string>('90')

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
  }, [isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      fetchLogs()
      fetchStats()
    }
  }, [isAuthenticated, page, levelFilter, loggerFilter, searchFilter])

  async function fetchLogs() {
    setLoading(true)
    setError(null)
    try {
      const response = await getLogEntries({
        skip: (page - 1) * 50,
        limit: 50,
        level: levelFilter || undefined,
        logger_name: loggerFilter || undefined,
        search: searchFilter || undefined,
      })
      setLogs(response.items)
      setTotal(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch log entries')
    } finally {
      setLoading(false)
    }
  }

  async function fetchStats() {
    try {
      const response = await getLogStats()
      setStats(response)
    } catch (err) {
      // Stats are optional — don't block the UI
      console.error('Failed to fetch stats:', err)
    }
  }

  async function handleCleanup() {
    if (!confirm(`Delete all log entries older than ${cleanupDays} days? This cannot be undone.`)) return
    setMessage(null)
    setError(null)
    try {
      const response = await cleanupLogs(parseInt(cleanupDays, 10))
      setMessage(response.message)
      fetchLogs()
      fetchStats()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cleanup logs')
    }
  }

  function clearFilters() {
    setLevelFilter('')
    setLoggerFilter('')
    setSearchFilter('')
    setPage(1)
  }

  function getLevelColor(level: string): string {
    switch (level) {
      case 'DEBUG': return 'text-slate-500'
      case 'INFO': return 'text-cyan-400'
      case 'WARNING': return 'text-amber-400'
      case 'ERROR': return 'text-red-400'
      case 'CRITICAL': return 'text-red-500 font-bold'
      default: return 'text-slate-400'
    }
  }

  function getLevelBadge(level: string): string {
    switch (level) {
      case 'DEBUG': return 'bg-slate-900/30 text-slate-400'
      case 'INFO': return 'bg-cyan-900/30 text-cyan-300'
      case 'WARNING': return 'bg-amber-900/30 text-amber-300'
      case 'ERROR': return 'bg-red-900/30 text-red-300'
      case 'CRITICAL': return 'bg-red-900/50 text-red-200'
      default: return 'bg-slate-900/30 text-slate-400'
    }
  }

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleString()
  }

  if (!isAuthenticated) return null

  const isSuperUser = user?.is_superuser

  if (!isSuperUser) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-200">
        <div className="mx-auto max-w-6xl px-6 py-12">
          <div className="rounded-2xl border border-red-900/30 bg-red-900/10 p-6 text-red-300">
            <h2 className="text-xl font-semibold mb-2">Access Denied</h2>
            <p>Logging history is only available to superusers.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="mt-4 text-4xl font-semibold">Logging History</h1>
            <p className="mt-2 text-slate-400">
              Review persisted application and system log entries
            </p>
          </div>
          <button
            onClick={fetchLogs}
            className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
          >
            Refresh
          </button>
        </div>

        {error && (
          <div className="mb-6 rounded-xl bg-red-900/50 border border-red-700 p-4 text-red-200">
            {error}
          </div>
        )}

        {message && (
          <div className="mb-6 rounded-xl bg-emerald-900/50 border border-emerald-700 p-4 text-emerald-200">
            {message}
          </div>
        )}

        {/* Stats Cards */}
        {stats && (
          <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-white/10 bg-slate-950/80 p-6">
              <p className="text-sm text-slate-400">Total Entries</p>
              <p className="mt-2 text-3xl font-bold">{stats.total_entries}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/80 p-6">
              <p className="text-sm text-slate-400">By Level</p>
              <div className="mt-2 space-y-1">
                {Object.entries(stats.by_level).map(([level, count]) => (
                  <div key={level} className="flex justify-between text-sm">
                    <span className={getLevelColor(level)}>{level}</span>
                    <span className="text-slate-300">{count as number}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/80 p-6">
              <p className="text-sm text-slate-400">Oldest Entry</p>
              <p className="mt-2 text-sm text-slate-300">
                {stats.oldest_entry ? formatDate(stats.oldest_entry) : 'N/A'}
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/80 p-6">
              <p className="text-sm text-slate-400">Newest Entry</p>
              <p className="mt-2 text-sm text-slate-300">
                {stats.newest_entry ? formatDate(stats.newest_entry) : 'N/A'}
              </p>
            </div>
          </div>
        )}

        {/* Top Loggers */}
        {stats && stats.top_loggers && stats.top_loggers.length > 0 && (
          <div className="mb-8 rounded-2xl border border-white/10 bg-slate-950/80 p-6">
            <h2 className="mb-4 text-lg font-semibold text-white">Top Loggers</h2>
            <div className="space-y-2">
              {stats.top_loggers.map((logger: { logger_name: string; count: number }) => (
                <div key={logger.logger_name} className="flex items-center gap-3">
                  <div className="w-48 truncate text-sm text-slate-400">{logger.logger_name}</div>
                  <div className="flex-1">
                    <div className="h-2 rounded-full bg-slate-800">
                      <div
                        className="h-2 rounded-full bg-cyan-500"
                        style={{
                          width: `${Math.max(
                            5,
                            (logger.count / (stats.total_entries || 1)) * 100,
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                  <span className="w-12 text-right text-sm text-slate-300">{logger.count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="mb-6 rounded-2xl border border-white/10 bg-slate-950/80 p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Filters</h2>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="text-sm text-cyan-400 hover:text-cyan-300"
            >
              {showFilters ? 'Hide' : 'Show'} Filters
            </button>
          </div>

          {showFilters && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Level</label>
                <select
                  value={levelFilter}
                  onChange={(e) => { setLevelFilter(e.target.value); setPage(1) }}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                >
                  <option value="">All Levels</option>
                  {LOG_LEVELS.map((level) => (
                    <option key={level} value={level}>{level}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Logger Name</label>
                <input
                  type="text"
                  value={loggerFilter}
                  onChange={(e) => setLoggerFilter(e.target.value)}
                  placeholder="Filter by logger name..."
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Search</label>
                <input
                  type="text"
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  placeholder="Search in messages..."
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>
              <div className="flex items-end gap-2">
                <button
                  onClick={clearFilters}
                  className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-400 hover:bg-slate-700 transition"
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Cleanup */}
        <div className="mb-8 rounded-2xl border border-red-900/30 bg-red-900/5 p-6">
          <h2 className="mb-2 text-lg font-semibold text-red-300">Log Cleanup</h2>
          <p className="mb-4 text-sm text-slate-400">
            Delete all log entries older than a specified number of days.
          </p>
          <div className="flex items-end gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Days</label>
              <input
                type="number"
                min="1"
                value={cleanupDays}
                onChange={(e) => setCleanupDays(e.target.value)}
                className="w-24 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <button
              onClick={handleCleanup}
              className="rounded-xl border border-red-700 bg-red-900/30 px-4 py-2 text-sm text-red-300 hover:bg-red-900/50 transition"
            >
              Delete Old Logs
            </button>
          </div>
        </div>

        {/* Logs Table */}
        <div className="rounded-3xl border border-white/10 bg-slate-950/80 shadow-2xl backdrop-blur-xl">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent"></div>
              <p className="mt-2 text-slate-400">Loading log entries...</p>
            </div>
          ) : logs.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-slate-400">No log entries found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Level</th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Logger</th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Message</th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Module</th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">User</th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className="border-b border-white/5 hover:bg-slate-900/50">
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getLevelBadge(log.level)}`}>
                          {log.level}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-300 truncate max-w-xs">{log.logger_name}</td>
                      <td className="px-6 py-4 text-sm text-slate-300">{log.message}</td>
                      <td className="px-6 py-4 text-sm text-slate-500">{log.module || '-'}</td>
                      <td className="px-6 py-4 text-sm text-slate-500">{log.user_id || '-'}</td>
                      <td className="px-6 py-4 text-sm text-slate-500">{formatDate(log.timestamp)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
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
