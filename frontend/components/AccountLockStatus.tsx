"use client"

import { useState, useEffect } from 'react'
import { getMyAccountLockStatus, AccountLockStatus as AccountLockStatusType } from '../lib/api'

interface AccountLockStatusProps {
  showDetails?: boolean
}

export default function AccountLockStatus({ showDetails = false }: AccountLockStatusProps) {
  const [status, setStatus] = useState<AccountLockStatusType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStatus()
  }, [])

  async function loadStatus() {
    try {
      const data = await getMyAccountLockStatus()
      setStatus(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load account status')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-4 bg-slate-700 rounded w-3/4"></div>
          <div className="h-3 bg-slate-700 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
        <p className="text-sm text-red-400">{error}</p>
      </div>
    )
  }

  if (!status) {
    return null
  }

  if (!status.is_locked) {
    return (
      <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-4">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm font-medium text-green-400">Account is active</p>
        </div>
        {showDetails && (
          <p className="text-xs text-slate-400 mt-1">
            Failed attempts: {status.failed_attempts}
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
      <div className="flex items-start gap-2">
        <svg className="w-5 h-5 text-red-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        <div className="flex-1">
          <p className="text-sm font-medium text-red-400">Account Locked</p>
          {status.reason && (
            <p className="text-xs text-red-300 mt-1">{status.reason}</p>
          )}
          {showDetails && status.locked_until && (
            <p className="text-xs text-slate-400 mt-1">
              Locked until: {new Date(status.locked_until).toLocaleString()}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}