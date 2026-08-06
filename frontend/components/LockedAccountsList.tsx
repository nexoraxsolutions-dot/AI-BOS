"use client"

import { useState, useEffect } from 'react'
import { getLockedAccounts, unlockAccount, LockedAccount } from '../lib/api'

export default function LockedAccountsList() {
  const [accounts, setAccounts] = useState<LockedAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [unlockingId, setUnlockingId] = useState<number | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  useEffect(() => {
    loadLockedAccounts()
  }, [])

  async function loadLockedAccounts() {
    try {
      const data = await getLockedAccounts(0, 50)
      setAccounts(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load locked accounts')
    } finally {
      setLoading(false)
    }
  }

  async function handleUnlock(userId: number) {
    setUnlockingId(userId)
    setMessage(null)
    
    try {
      await unlockAccount(userId)
      setMessage({ type: 'success', text: 'Account unlocked successfully' })
      // Remove from list
      setAccounts(prev => prev.filter(account => account.id !== userId))
    } catch (err) {
      setMessage({ 
        type: 'error', 
        text: err instanceof Error ? err.message : 'Failed to unlock account' 
      })
    } finally {
      setUnlockingId(null)
    }
  }

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-slate-700 rounded w-1/4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-slate-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6">
        <p className="text-sm text-red-400">{error}</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Locked Accounts</h3>
      
      {message && (
        <div className={`mb-4 rounded-lg p-3 ${
          message.type === 'success' 
            ? 'bg-green-500/10 border border-green-500/30' 
            : 'bg-red-500/10 border border-red-500/30'
        }`}>
          <p className={`text-sm ${message.type === 'success' ? 'text-green-400' : 'text-red-400'}`}>
            {message.text}
          </p>
        </div>
      )}

      {accounts.length === 0 ? (
        <p className="text-sm text-slate-400">No locked accounts</p>
      ) : (
        <div className="space-y-3">
          {accounts.map(account => (
            <div 
              key={account.id} 
              className="rounded-lg border border-slate-700 bg-slate-950/50 p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-white">
                      {account.full_name || account.username || 'Unknown User'}
                    </p>
                    <span className="inline-flex items-center rounded-full bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-400">
                      Locked
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{account.email}</p>
                  {account.lock_reason && (
                    <p className="text-xs text-red-300 mt-1">{account.lock_reason}</p>
                  )}
                  {account.locked_until && (
                    <p className="text-xs text-slate-400 mt-1">
                      Locked until: {new Date(account.locked_until).toLocaleString()}
                    </p>
                  )}
                  <p className="text-xs text-slate-500 mt-1">
                    Failed attempts: {account.failed_login_attempts}
                  </p>
                </div>
                
                <button
                  onClick={() => handleUnlock(account.id)}
                  disabled={unlockingId === account.id}
                  className="ml-4 rounded-lg bg-cyan-500 px-3 py-1.5 text-xs font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {unlockingId === account.id ? 'Unlocking...' : 'Unlock'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}