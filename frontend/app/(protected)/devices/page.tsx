'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '../../../context/AuthContext'
import {
  getDevices,
  getDeviceStats,
  revokeDevice,
  revokeAllDevices,
  markDeviceCurrent,
  DeviceOut,
  DeviceStats,
} from '../../../lib/api'

export default function DevicesPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuth()

  const [devices, setDevices] = useState<DeviceOut[]>([])
  const [stats, setStats] = useState<DeviceStats | null>(null)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [includeRevoked, setIncludeRevoked] = useState(false)
  const [actionLoading, setActionLoading] = useState<number | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
    loadData()
  }, [isAuthenticated, router, includeRevoked])

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const [devicesRes, statsRes] = await Promise.all([
        getDevices({ include_revoked: includeRevoked }),
        getDeviceStats(),
      ])
      setDevices(devicesRes.items)
      setTotal(devicesRes.total)
      setStats(statsRes)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load devices')
    } finally {
      setLoading(false)
    }
  }

  async function handleRevoke(deviceId: number) {
    if (!confirm('Are you sure you want to revoke this device? You will be logged out from it.')) return
    setActionLoading(deviceId)
    try {
      await revokeDevice(deviceId)
      setMessage('Device revoked successfully')
      setDevices(devices.filter(d => d.id !== deviceId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke device')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleRevokeAll() {
    if (!confirm('Are you sure you want to revoke ALL devices? You will be logged out from all sessions.')) return
    setActionLoading(-1)
    try {
      const res = await revokeAllDevices()
      setMessage(res.message)
      setDevices([])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke all devices')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleMarkCurrent(deviceId: number) {
    setActionLoading(deviceId)
    try {
      await markDeviceCurrent(deviceId)
      setMessage('Device marked as current')
      setDevices(devices.map(d => ({ ...d, is_current: d.id === deviceId })))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to mark device')
    } finally {
      setActionLoading(null)
    }
  }

  function formatDate(dateStr?: string) {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleString()
  }

  function getDeviceIcon(deviceType?: string) {
    if (deviceType === 'mobile') return '📱'
    if (deviceType === 'tablet') return '💻'
    return '🖥️'
  }

  if (!isAuthenticated) return null

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="mt-4 text-4xl font-semibold">Device Management</h1>
            <p className="mt-2 text-slate-400">
              Manage your active sessions and devices
            </p>
          </div>
          <Link
            href="/profile"
            className="rounded-2xl border border-slate-700 bg-slate-900 px-5 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
          >
            Back to Profile
          </Link>
        </div>

        {error && (
          <div className="mb-6 rounded-xl bg-red-900/50 border border-red-700 p-4 text-red-200" role="alert">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {message && (
          <div className="mb-6 rounded-xl bg-emerald-900/50 border border-emerald-700 p-4 text-emerald-200" role="alert">
            <p className="text-sm">{message}</p>
          </div>
        )}

        {/* Stats Cards */}
        {stats && (
          <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-white/10 bg-slate-950/80 p-6">
              <p className="text-sm text-slate-400">Total Devices</p>
              <p className="mt-2 text-3xl font-bold">{stats.total_devices}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/80 p-6">
              <p className="text-sm text-slate-400">Active</p>
              <p className="mt-2 text-3xl font-bold text-emerald-400">{stats.active_devices}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/80 p-6">
              <p className="text-sm text-slate-400">Revoked</p>
              <p className="mt-2 text-3xl font-bold text-red-400">{stats.revoked_devices}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/80 p-6">
              <p className="text-sm text-slate-400">Expiring Soon</p>
              <p className="mt-2 text-3xl font-bold text-amber-400">{stats.expiring_soon}</p>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="mb-6 flex items-center justify-between">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeRevoked}
              onChange={(e) => setIncludeRevoked(e.target.checked)}
              className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500"
            />
            <span className="text-sm text-slate-300">Include revoked devices</span>
          </label>
          <button
            onClick={handleRevokeAll}
            disabled={actionLoading === -1 || devices.length === 0}
            className="rounded-2xl bg-red-600 px-5 py-2 text-sm font-semibold text-white hover:bg-red-500 disabled:opacity-50"
          >
            {actionLoading === -1 ? 'Revoking...' : 'Revoke All Devices'}
          </button>
        </div>

        {/* Devices Table */}
        <div className="rounded-3xl border border-white/10 bg-slate-950/80 shadow-2xl backdrop-blur-xl">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent"></div>
              <p className="mt-2 text-slate-400">Loading devices...</p>
            </div>
          ) : devices.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-slate-400">No devices found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                      Device
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                      Browser / OS
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                      IP Address
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                      Last Used
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                      Created
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-medium uppercase tracking-wider text-slate-400">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {devices.map((device) => (
                    <tr key={device.id} className="border-b border-white/5 hover:bg-slate-900/50">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{getDeviceIcon(device.device_type)}</span>
                          <div>
                            <p className="font-medium">{device.device_name || 'Unknown Device'}</p>
                            <p className="text-sm text-slate-500">{device.device_type || 'unknown'}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm">{device.browser || 'Unknown'}</p>
                        <p className="text-sm text-slate-500">{device.os || 'Unknown'}</p>
                      </td>
                      <td className="px-6 py-4">
                        <code className="text-sm text-slate-300">{device.client_ip || 'N/A'}</code>
                      </td>
                      <td className="px-6 py-4">
                        {device.is_revoked ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium text-red-300">
                            <span className="h-1.5 w-1.5 rounded-full bg-red-400"></span>
                            Revoked
                          </span>
                        ) : device.is_current ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium text-emerald-300">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
                            Current
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium text-slate-400">
                            <span className="h-1.5 w-1.5 rounded-full bg-slate-500"></span>
                            Active
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-400">
                        {formatDate(device.last_used_at)}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-400">
                        {formatDate(device.created_at)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {!device.is_revoked && !device.is_current && (
                            <button
                              onClick={() => handleMarkCurrent(device.id)}
                              disabled={actionLoading === device.id}
                              className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800 disabled:opacity-50"
                            >
                              {actionLoading === device.id ? '...' : 'Mark Current'}
                            </button>
                          )}
                          {!device.is_revoked && (
                            <button
                              onClick={() => handleRevoke(device.id)}
                              disabled={actionLoading === device.id}
                              className="rounded-xl border border-red-700 bg-red-900/30 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-900/50 disabled:opacity-50"
                            >
                              {actionLoading === device.id ? '...' : 'Revoke'}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <p className="mt-6 text-center text-sm text-slate-400">
          <Link href="/profile" className="text-cyan-400 hover:text-cyan-300 font-medium transition">
            Back to Profile
          </Link>
        </p>
      </div>
    </main>
  )
}
