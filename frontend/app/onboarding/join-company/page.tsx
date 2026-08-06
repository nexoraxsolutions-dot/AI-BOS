"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '../../../context/AuthContext'
import { getInvitation, acceptInvitation, CompanyInvitationDetail } from '../../../lib/api'
import { ArrowLeft, UserPlus, Loader2, CheckCircle2, Link2 } from 'lucide-react'

function extractToken(input: string): string {
  const trimmed = input.trim()
  // If a full link is pasted, use the last path segment (the token).
  const matches = trimmed.match(/\/([^/?#]+)\/?([?#].*)?$/)
  if (matches && matches[1] && !trimmed.includes(' ')) {
    return matches[1]
  }
  return trimmed
}

export default function JoinCompanyPage() {
  const { isAuthenticated, loading, refreshUser } = useAuth()
  const router = useRouter()

  const [input, setInput] = useState('')
  const [mode, setMode] = useState<'link' | 'code'>('link')
  const [invitation, setInvitation] = useState<CompanyInvitationDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [joining, setJoining] = useState(false)
  const [joined, setJoined] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, loading, router])

  if (loading || !isAuthenticated) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent" />
      </main>
    )
  }

  async function handleLookup() {
    setError(null)
    setInvitation(null)
    const token = extractToken(input)
    if (!token) {
      setError('Please paste your invitation link or enter your invitation code.')
      return
    }
    setLoadingDetails(true)
    try {
      const detail = await getInvitation(token)
      setInvitation(detail)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invitation not found or no longer valid.')
    } finally {
      setLoadingDetails(false)
    }
  }

  async function handleJoin() {
    setError(null)
    setJoining(true)
    try {
      const token = extractToken(input)
      const result = await acceptInvitation(token)
      await refreshUser()
      setJoined(
        result.company_name
          ? `You have joined ${result.company_name}`
          : 'You have joined the company successfully',
      )
      setTimeout(() => router.push('/dashboard'), 1200)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to accept invitation.')
    } finally {
      setJoining(false)
    }
  }

  const inputCls =
    'w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition'

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-12">
      <div className="w-full max-w-xl">
        <Link href="/onboarding" className="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-cyan-300">
          <ArrowLeft size={16} /> Back to onboarding
        </Link>

        <div className="rounded-3xl border border-white/10 bg-slate-950/80 p-8 shadow-2xl backdrop-blur-xl sm:p-10">
          {joined ? (
            <div className="py-10 text-center">
              <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/40">
                <CheckCircle2 className="h-8 w-8 text-emerald-400" />
              </div>
              <h2 className="text-2xl font-semibold text-white">Invitation accepted!</h2>
              <p className="mt-2 text-sm text-slate-400">{joined}. Taking you to your dashboard...</p>
            </div>
          ) : (
            <>
              <div className="mb-6 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/15 text-cyan-400">
                  <UserPlus size={22} />
                </div>
                <div>
                  <h1 className="text-2xl font-semibold text-white">Join Existing Company</h1>
                  <p className="text-sm text-slate-400">Use your invitation to join a company</p>
                </div>
              </div>

              <div className="mb-5 grid grid-cols-2 gap-2 rounded-xl bg-slate-900 p-1">
                <button
                  type="button"
                  onClick={() => { setMode('link'); setInput(''); setInvitation(null); setError(null); }}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition ${mode === 'link' ? 'bg-cyan-500 text-slate-950' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  Invitation Link
                </button>
                <button
                  type="button"
                  onClick={() => { setMode('code'); setInput(''); setInvitation(null); setError(null); }}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition ${mode === 'code' ? 'bg-cyan-500 text-slate-950' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  Invitation Code
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="mb-1 block text-sm text-slate-300">
                    {mode === 'link' ? 'Invitation Link' : 'Invitation Code'}
                  </label>
                  <div className="flex gap-2">
                    <input
                      value={input}
                      onChange={(e) => { setInput(e.target.value); setInvitation(null); setError(null); }}
                      placeholder={
                        mode === 'link'
                          ? 'https://aibos.app/join/TOKEN'
                          : 'Enter your invitation code'
                      }
                      className={inputCls}
                    />
                    <button
                      type="button"
                      onClick={handleLookup}
                      disabled={loadingDetails || !input.trim()}
                      className="inline-flex items-center gap-1.5 rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loadingDetails ? <Loader2 size={16} className="animate-spin" /> : <Link2 size={16} />}
                      Check
                    </button>
                  </div>
                </div>

                {error && (
                  <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
                    {error}
                  </div>
                )}

                {invitation && (
                  <div className="rounded-xl border border-white/10 bg-slate-900 p-5">
                    <p className="text-xs uppercase tracking-wider text-slate-500">Invitation</p>
                    <p className="mt-1 text-lg font-semibold text-white">{invitation.company_name}</p>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-400">
                      <span className="rounded-full bg-white/5 px-3 py-1">Role: {invitation.role}</span>
                      <span className="rounded-full bg-white/5 px-3 py-1">Status: {invitation.status}</span>
                    </div>
                    <button
                      onClick={handleJoin}
                      disabled={joining}
                      className="mt-5 w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
                    >
                      {joining ? (
                        <>
                          <Loader2 size={18} className="animate-spin" /> Joining...
                        </>
                      ) : (
                        'Join Company'
                      )}
                    </button>
                  </div>
                )}

                <p className="text-center text-sm text-slate-500">
                  Starting fresh instead?{' '}
                  <Link href="/onboarding/create-company" className="text-cyan-400 hover:text-cyan-300">
                    Create a company
                  </Link>
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  )
}
