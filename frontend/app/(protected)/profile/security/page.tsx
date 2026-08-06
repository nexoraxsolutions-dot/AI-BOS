"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '../../../context/AuthContext'
import { getMyProfile, get2FAStatus, getSessions, getMyAuditLogs, getApiKeys, getBackupCodesRemaining } from '../../../lib/api'
import { Mail, Lock, Monitor, Clock, Key, FileText, Loader2, CheckCircle2, XCircle } from 'lucide-react'

function Section({ title, icon, loading, error, children }: any) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-5 sm:p-6">
      <div className="mb-4 flex items-center gap-2 text-slate-200">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/5 text-slate-400">{icon}</span>
        <h3 className="text-base font-semibold">{title}</h3>
      </div>
      {loading ? <div className="flex items-center gap-2 text-sm text-slate-400"><Loader2 size={16} className="animate-spin" /> Loading...</div> : error ? <p className="text-sm text-red-400">{error}</p> : children}
    </div>
  )
}

export default function ProfileSecurityPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuth()

  const [profile, setProfile] = useState<User | null>(null)
  const [twoFA, setTwoFA] = useState<{ is_2fa_enabled: boolean } | null>(null)
  const [sessions, setSessions] = useState<SessionListResponse | null>(null)
  const [logs, setLogs] = useState<AuditLogListResponse | null>(null)
  const [apiKeys, setApiKeys] = useState<ApiKeyListResponse | null>(null)
  const [backupRemaining, setBackupRemaining] = useState<number | null>(null)

  const [profileLoading, setProfileLoading] = useState(true)
  const [twoFALoading, setTwoFALoading] = useState(true)
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [logsLoading, setLogsLoading] = useState(true)
  const [apiKeysLoading, setApiKeysLoading] = useState(true)
  const [backupLoading, setBackupLoading] = useState(true)

  const [profileError, setProfileError] = useState<string | null>(null)
  const [twoFAError, setTwoFAError] = useState<string | null>(null)
  const [sessionsError, setSessionsError] = useState<string | null>(null)
  const [logsError, setLogsError] = useState<string | null>(null)
  const [apiKeysError, setApiKeysError] = useState<string | null>(null)
  const [backupError, setBackupError] = useState<string | null>(null)


  useEffect(() => { if (!isAuthenticated) router.push('/') }, [isAuthenticated, router])

  useEffect(() => {
    let c = false
    ;(async () => {
      try { const p = await getMyProfile(); if (!c) { setProfile(p); setProfileError(null) } }
      catch (err) { if (!c) setProfileError(err instanceof Error ? err.message : 'Failed to load profile') }
      finally { if (!c) setProfileLoading(false) }
    })()
    return () => { c = true }
  }, [])

  useEffect(() => {
    let c = false
    ;(async () => {
      try { const s = await get2FAStatus(); if (!c) { setTwoFA(s); setTwoFAError(null) } }
      catch (err) { if (!c) setTwoFAError(err instanceof Error ? err.message : 'Failed to load 2FA') }
      finally { if (!c) setTwoFALoading(false) }
    })()
    return () => { c = true }
  }, [])

  useEffect(() => {
    let c = false
    ;(async () => {
      try { const s = await getSessions(0, 5, true); if (!c) { setSessions(s); setSessionsError(null) } }
      catch (err) { if (!c) setSessionsError(err instanceof Error ? err.message : 'Failed to load sessions') }
      finally { if (!c) setSessionsLoading(false) }
    })()
    return () => { c = true }
  }, [])

  useEffect(() => {
    let c = false
    ;(async () => {
      try { const l = await getMyAuditLogs({ skip: 0, limit: 5 }); if (!c) { setLogs(l); setLogsError(null) } }
      catch (err) { if (!c) setLogsError(err instanceof Error ? err.message : 'Failed to load logs') }
      finally { if (!c) setLogsLoading(false) }
    })()
    return () => { c = true }
  }, [])
  useEffect(() => {
    let c = false
    ;(async () => {
      try { const a = await getApiKeys(0, 5, true); if (!c) { setApiKeys(a); setApiKeysError(null) } }
      catch (err) { if (!c) setApiKeysError(err instanceof Error ? err.message : 'Failed to load API keys') }
      finally { if (!c) setApiKeysLoading(false) }
    })()
    return () => { c = true }
  }, [])

  useEffect(() => {
    let c = false
    ;(async () => {
      try { const b = await getBackupCodesRemaining(); if (!c) { setBackupRemaining(b.remaining); setBackupError(null) } }
      catch (err) { if (!c) setBackupError(err instanceof Error ? err.message : 'Failed to load backup codes') }
      finally { if (!c) setBackupLoading(false) }
    })()
    return () => { c = true }
  }, [])

  if (!isAuthenticated) return null
  const fmt = (d?: string | null) => (d ? new Date(d).toLocaleString() : 'N/A')
  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
          <h1 className="mt-2 text-3xl font-semibold text-white">Security</h1>
          <p className="mt-1 text-sm text-slate-400">Manage your email verification, two-factor authentication, sessions, and API access.</p>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Section title="Email Verification" icon={<Mail size={18} />} loading={profileLoading} error={profileError}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-300">Status: <span className={profile?.is_email_verified ? 'text-emerald-300' : 'text-amber-300'}>{profile?.is_email_verified ? 'Verified' : 'Unverified'}</span></p>
                <p className="mt-1 text-xs text-slate-500">{profile?.email}</p>
              </div>
              {profile?.is_email_verified ? <CheckCircle2 className="text-emerald-400" size={22} /> : <XCircle className="text-amber-400" size={22} />}
            </div>
            {!profile?.is_email_verified && (
              <div className="mt-4">
                <Link href="/verify-email" className="inline-flex items-center gap-1.5 rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400">Verify Email</Link>
             )}
          </Section>

          <Section title="Two-Factor Authentication" icon={<Lock size={18} />} loading={twoFALoading} error={twoFAError}>
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-300">Status: <span className={twoFA?.is_2fa_enabled ? 'text-emerald-300' : 'text-amber-300'}>{twoFA?.is_2fa_enabled ? 'Enabled' : 'Disabled'}</span></p>
              {twoFA?.is_2fa_enabled ? <CheckCircle2 className="text-emerald-400" size={22} /> : <XCircle className="text-amber-400" size={22} />}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link href="/two-factor-setup" className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-white/10">{twoFA?.is_2fa_enabled ? 'Manage 2FA' : 'Enable 2FA'}</Link>
              {twoFA?.is_2fa_enabled && backupRemaining !== null && (
                <span className="inline-flex items-center gap-1 rounded-xl bg-white/5 px-3 py-2 text-xs text-slate-400"><Key size={14} /> {backupRemaining} backup codes left</span>
              )}
            </div>
          </Section>
          <Section title="Active Sessions" icon={<Monitor size={18} />} loading={sessionsLoading} error={sessionsError}>
            <div className="space-y-2">
              {sessions?.items.slice(0, 3).map((s) => (
                <div key={s.id} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2">
                  <div className="min-w-0">
                    <p className="truncate text-sm text-slate-300">{s.device_name || s.user_agent || `Session #${s.id}`}</p>
                    <p className="text-xs text-slate-500">{s.ip_address ?? 'N/A'} · {fmt(s.last_activity_at)}</p>
                  </div>
                  <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs ${s.is_active ? 'bg-emerald-500/10 text-emerald-300' : 'bg-gray-500/10 text-gray-400'}`}>{s.is_active ? 'Active' : 'Inactive'}</span>
                </div>
              ))}
              {(!sessions || sessions.items.length === 0) && <p className="text-sm text-slate-500">No sessions found.</p>}
            </div>
            <div className="mt-4">
              <button className="text-sm text-slate-500">View all sessions</button>
            </div>
          </Section>

          <Section title="Login History" icon={<Clock size={18} />} loading={logsLoading} error={logsError}>
            <div className="space-y-2">
              {logs?.items.slice(0, 3).map((l) => (
                <div key={l.id} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2">
                  <div className="min-w-0">
                    <p className="truncate text-sm text-slate-300">{l.action}</p>
                    <p className="text-xs text-slate-500">{l.ip_address ?? 'N/A'} · {fmt(l.created_at)}</p>
                  </div>
                  <span className="shrink-0 rounded-full bg-white/5 px-2.5 py-0.5 text-xs text-slate-400">#{l.id}</span>
                </div>
              ))}
              {(!logs || logs.items.length === 0) && <p className="text-sm text-slate-500">No login history available.</p>}
            </div>
            <div className="mt-4">
              <button className="text-sm text-slate-500">View full history</button>
            </div>
          </Section>

          <Section title="API Keys" icon={<Key size={18} />} loading={apiKeysLoading} error={apiKeysError}>
            <div className="space-y-2">
              {apiKeys?.items.slice(0, 3).map((k) => (
                <div key={k.id} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2">
                  <div className="min-w-0">
                    <p className="truncate text-sm text-slate-300">{k.key_name}</p>
                    <p className="text-xs text-slate-500">{k.is_active ? 'Active' : 'Revoked'} · Last used {k.last_used_at ? fmt(k.last_used_at) : 'never'}</p>
                  </div>
                  <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs ${k.is_active ? 'bg-emerald-500/10 text-emerald-300' : 'bg-red-500/10 text-red-300'}`}>{k.is_active ? 'Active' : 'Revoked'}</span>
                </div>
              ))}
              {(!apiKeys || apiKeys.items.length === 0) && <p className="text-sm text-slate-500">No API keys yet.</p>}
            </div>
            <div className="mt-4">
              <button className="text-sm text-slate-500">Manage API keys</button>
            </div>
          </Section>

          <Section title="Recovery Codes" icon={<FileText size={18} />} loading={backupLoading} error={backupError}>
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-300">Remaining backup codes: <span className={backupRemaining && backupRemaining > 0 ? 'text-emerald-300' : 'text-amber-300'}>{backupRemaining ?? '—'}</span></p>
              {twoFA?.is_2fa_enabled ? <CheckCircle2 className="text-emerald-400" size={22} /> : <XCircle className="text-slate-500" size={22} />}
            </div>
            <p className="mt-2 text-xs text-slate-500">{twoFA?.is_2fa_enabled ? 'You can regenerate backup codes from the Two-Factor Authentication page.' : 'Enable two-factor authentication to generate recovery codes.'}</p>
            <div className="mt-4">
              <Link href="/two-factor-setup" className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-white/10">{twoFA?.is_2fa_enabled ? 'Regenerate Backup Codes' : 'Enable 2FA'}</Link>
            </div>
          </Section>
        </div>
      </div>
    </main>
  )
}
