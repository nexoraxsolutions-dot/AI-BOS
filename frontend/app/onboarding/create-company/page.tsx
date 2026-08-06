"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '../../../context/AuthContext'
import { onboardCompany, OnboardCompanyResponse } from '../../../lib/api'
import { ArrowLeft, Building2, Loader2, CheckCircle2 } from 'lucide-react'

const INDUSTRIES = [
  'Technology', 'Finance', 'Healthcare', 'Retail', 'Manufacturing',
  'Education', 'Real Estate', 'Transportation', 'Hospitality', 'Other',
]

const SIZES = [
  { label: '1 - 10 employees', value: 10 },
  { label: '11 - 50 employees', value: 50 },
  { label: '51 - 200 employees', value: 200 },
  { label: '201 - 500 employees', value: 500 },
  { label: '500+ employees', value: 1000 },
]

const TIMEZONES = [
  'UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
  'Europe/London', 'Europe/Berlin', 'Europe/Paris', 'Asia/Dubai', 'Asia/Kolkata',
  'Asia/Singapore', 'Asia/Tokyo', 'Australia/Sydney',
]

const CURRENCIES = ['USD', 'EUR', 'GBP', 'AED', 'INR', 'SGD', 'JPY', 'AUD']

function slugifyDomain(name: string): string {
  const base = name.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  return base || 'company'
}

export default function CreateCompanyPage() {
  const { isAuthenticated, loading, refreshUser } = useAuth()
  const router = useRouter()

  const [form, setForm] = useState({
    name: '',
    industry: '',
    size: '',
    country: '',
    timezone: 'UTC',
    currency: 'USD',
    logo_url: '',
    website: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState<OnboardCompanyResponse | null>(null)

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

  const update = (key: string, value: string) => setForm((f) => ({ ...f, [key]: value }))

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const data = await onboardCompany({
        name: form.name.trim(),
        domain: slugifyDomain(form.name),
        industry: form.industry || undefined,
        employee_count: form.size ? Number(form.size) : undefined,
        website: form.website.trim() || undefined,
        logo_url: form.logo_url.trim() || undefined,
        settings: {
          country: form.country.trim() || undefined,
          timezone: form.timezone,
          currency: form.currency,
        },
      })
      setSuccess(data)
      await refreshUser()
      setTimeout(() => router.push('/dashboard'), 1200)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create company')
    } finally {
      setSubmitting(false)
    }
  }

  const inputCls =
    'w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition'

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-12">
      <div className="w-full max-w-2xl">
        <Link href="/onboarding" className="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-cyan-300">
          <ArrowLeft size={16} /> Back to onboarding
        </Link>

        <div className="rounded-3xl border border-white/10 bg-slate-950/80 p-8 shadow-2xl backdrop-blur-xl sm:p-10">
          {success ? (
            <div className="py-10 text-center">
              <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/40">
                <CheckCircle2 className="h-8 w-8 text-emerald-400" />
              </div>
              <h2 className="text-2xl font-semibold text-white">Company created!</h2>
              <p className="mt-2 text-sm text-slate-400">
                <span className="font-medium text-cyan-300">{success.name}</span> is ready. Taking you to your dashboard...
              </p>
            </div>
          ) : (
            <>
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="mb-1 block text-sm text-slate-300">Company Name *</label>
                  <input
                    value={form.name}
                    onChange={(e) => update('name', e.target.value)}
                    required
                    placeholder="Acme Corporation"
                    className={inputCls}
                  />
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm text-slate-300">Industry</label>
                    <select
                      value={form.industry}
                      onChange={(e) => update('industry', e.target.value)}
                      className={inputCls}
                    >
                      <option value="">Select industry</option>
                      {INDUSTRIES.map((i) => (
                        <option key={i} value={i}>{i}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm text-slate-300">Company Size</label>
                    <select
                      value={form.size}
                      onChange={(e) => update('size', e.target.value)}
                      className={inputCls}
                    >
                      <option value="">Select size</option>
                      {SIZES.map((s) => (
                        <option key={s.value} value={s.value}>{s.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm text-slate-300">Country</label>
                    <input
                      value={form.country}
                      onChange={(e) => update('country', e.target.value)}
                      placeholder="United States"
                      className={inputCls}
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm text-slate-300">Timezone</label>
                    <select
                      value={form.timezone}
                      onChange={(e) => update('timezone', e.target.value)}
                      className={inputCls}
                    >
                      {TIMEZONES.map((tz) => (
                        <option key={tz} value={tz}>{tz}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm text-slate-300">Currency</label>
                    <select
                      value={form.currency}
                      onChange={(e) => update('currency', e.target.value)}
                      className={inputCls}
                    >
                      {CURRENCIES.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm text-slate-300">Logo URL <span className="text-slate-500">(optional)</span></label>
                    <input
                      value={form.logo_url}
                      onChange={(e) => update('logo_url', e.target.value)}
                      placeholder="https://.../logo.png"
                      className={inputCls}
                    />
                  </div>
                </div>
                <div>
                  <label className="mb-1 block text-sm text-slate-300">Website <span className="text-slate-500">(optional)</span></label>
                  <input
                    value={form.website}
                    onChange={(e) => update('website', e.target.value)}
                    placeholder="https://acme.com"
                    className={inputCls}
                  />
                </div>

                {error && (
                  <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={submitting || !form.name.trim()}
                  className="w-full rounded-2xl bg-cyan-500 px-5 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
                >
                  {submitting ? (
                    <>
                      <Loader2 size={18} className="animate-spin" /> Creating...
                    </>
                  ) : (
                    'Create Company'
                  )}
                </button>

                <p className="text-center text-sm text-slate-500">
                  Have an invitation instead?{' '}
                  <Link href="/onboarding/join-company" className="text-cyan-400 hover:text-cyan-300">
                    Join an existing company
                  </Link>
                </p>
              </form>
            </>
          )}
        </div>
      </div>
    </main>
  )
}

