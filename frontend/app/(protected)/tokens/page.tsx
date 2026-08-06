"use client"

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../../context/AuthContext'
import { useRouter } from 'next/navigation'
import { getTokens, revokeToken, revokeAllTokens, cleanupTokens, TokenInfo, TokenListResponse } from '../../../lib/api'

export default function TokensPage() {
  const { isAuthenticated, token } = useAuth()
  const router = useRouter()
  const [tokens, setTokens] = useState<TokenInfo[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [includeRevoked, setIncludeRevoked] = useState(false)
  const [showRevokeAllConfirm, setShowRevokeAllConfirm] = useState(false)
  const [revokingId, setRevokingId] = useState<number | null>(null)

  const fetchTokens = useCallback(async () => {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      const data = await getTokens((page - 1) * pageSize, pageSize, includeRevoked)
      setTokens(data.items)
      setTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tokens')
    } finally {
      setLoading(false)
    }
  }, [token, page, pageSize, includeRevoked])

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }
    fetchTokens()
  }, [isAuthenticated, router, fetchTokens])

  const handleRevoke = async (tokenId: number) => {
    setRevokingId(tokenId)
    setError('')
    setSuccess('')
    try {
      await revokeToken(tokenId)
      setSuccess('Token revoked successfully')
      fetchTokens()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke token')
    } finally {
      setRevokingId(null)
    }
  }

  const handleRevokeAll = async () => {
    setError('')
    setSuccess('')
    try {
      const data = await revokeAllTokens()
      setSuccess(data.message || 'All tokens revoked successfully')
      setShowRevokeAllConfirm(false)
      fetchTokens()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke all tokens')
    }
  }

  const handleCleanup = async () => {
    setError('')
    setSuccess('')
    try {
      const data = await cleanupTokens()
      setSuccess(data.message || 'Expired tokens cleaned up')
      fetchTokens()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cleanup tokens')
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

  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-white">Token Management</h1>
            <p className="mt-2 text-slate-400">Manage your active sessions and refresh tokens</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleCleanup}
              className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition"
            >
              Cleanup Expired
            </button>
            <button
              onClick={() => setShowRevokeAllConfirm(true)}
              className="rounded-xl border border-red-700 bg-red-900/50 px-4 py-2 text-sm text-red-300 hover:bg-red-800 hover:text-red-200 transition"
            >
              Revoke All
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

        <div className="mb-6 flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={includeRevoked}
              onChange={(e) => {
                setIncludeRevoked(e.target.checked)
                setPage(1)
              }}
              className="rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-cyan-500/20"
            />
            Include revoked tokens
          </label>
          <span className="text-sm text-slate-500">
            {total} token{total !== 1 ? 's' : ''} found
          </span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent" />
          </div>
        ) : tokens.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-12 text-center">
            <p className="text-slate-400">No tokens found</p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-white/10">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 bg-slate-900/80">
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">ID</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Type</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Status</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Created</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">Expires</th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">IP Address</th>
                  <th className="px-4 py-3 text-right text-slate-400 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {tokens.map((t) => {
                  const expired = isExpired(t.expires_at)
                  const revoked = t.is_revoked
                  return (
                    <tr key={t.id} className="border-b border-white/5 hover:bg-white/5 transition">
                      <td className="px-4 py-3 text-slate-300">{t.id}</td>
                      <td className="px-4 py-3">
                        <span className="rounded-full bg-cyan-500/10 px-2.5 py-0.5 text-xs text-cyan-300">
                          {t.token_type}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {revoked ? (
                          <span className="rounded-full bg-red-500/10 px-2.5 py-0.5 text-xs text-red-400">Revoked</span>
                        ) : expired ? (
                          <span className="rounded-full bg-yellow-500/10 px-2.5 py-0.5 text-xs text-yellow-400">Expired</span>
                        ) : (
                          <span className="rounded-full bg-green-500/10 px-2.5 py-0.5 text-xs text-green-400">Active</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-400">{formatDate(t.created_at)}</td>
                      <td className={`px-4 py-3 ${expired ? 'text-yellow-400' : 'text-slate-400'}`}>
                        {formatDate(t.expires_at)}
                      </td>
                      <td className="px-4 py-3 text-slate-400 font-mono text-xs">{t.client_ip || 'N/A'}</td>
                      <td className="px-4 py-3 text-right">
                        {!revoked && !expired && (
                          <button
                            onClick={() => handleRevoke(t.id)}
                            disabled={revokingId === t.id}
                            className="rounded-lg bg-red-500/10 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/20 transition disabled:opacity-50"
                          >
                            {revokingId === t.id ? 'Revoking...' : 'Revoke'}
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

        {showRevokeAllConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
              <h3 className="text-lg font-semibold text-white">Revoke All Tokens</h3>
              <p className="mt-2 text-sm text-slate-400">
                This will revoke all your active refresh tokens. You will need to log in again on all devices.
              </p>
              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={() => setShowRevokeAllConfirm(false)}
                  className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRevokeAll}
                  className="rounded-xl bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-500 transition"
                >
                  Revoke All
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}