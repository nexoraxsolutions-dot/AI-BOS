"use client"

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '../../context/AuthContext'
import { Building2, UserPlus, Sparkles, ArrowRight } from 'lucide-react'

export default function OnboardingPage() {
  const { isAuthenticated, loading, user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login')
      return
    }
    // Already has a company — nothing to onboard.
    if (!loading && isAuthenticated && user && (user.company_id || user.is_superuser)) {
      router.push('/dashboard')
    }
  }, [isAuthenticated, loading, user, router])

  if (loading || !isAuthenticated) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent" />
      </main>
    )
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-950 px-6 py-12">
      <div className="w-full max-w-3xl rounded-3xl border border-white/10 bg-slate-950/80 p-8 text-center shadow-2xl backdrop-blur-xl sm:p-12">
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-500/10 border border-cyan-500/40">
          <Sparkles className="text-cyan-400" size={26} />
        </div>
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-400">AI-BOS</p>
        <h1 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">Welcome to AI-BOS</h1>
        <p className="mx-auto mt-3 max-w-xl text-slate-400">
          You&apos;re almost there. Set up your workspace to start managing your company with AI-BOS.
        </p>
        <p className="mt-8 text-base font-medium text-slate-300">How would you like to continue?</p>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <Link
            href="/onboarding/create-company"
            className="group flex flex-col items-start gap-3 rounded-2xl border border-white/10 bg-white/5 p-6 text-left transition hover:border-cyan-500/50 hover:bg-white/10"
          >
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/15 text-cyan-400">
              <Building2 size={22} />
            </span>
            <span>
              <span className="block text-base font-semibold text-white">Create Company</span>
              <span className="mt-1 block text-sm text-slate-400">
                Start a brand new organization and become its owner.
              </span>
            </span>
            <span className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-cyan-400 group-hover:text-cyan-300">
              Get started <ArrowRight size={16} />
            </span>
          </Link>

          <Link
            href="/onboarding/join-company"
            className="group flex flex-col items-start gap-3 rounded-2xl border border-white/10 bg-white/5 p-6 text-left transition hover:border-cyan-500/50 hover:bg-white/10"
          >
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/15 text-cyan-400">
              <UserPlus size={22} />
            </span>
            <span>
              <span className="block text-base font-semibold text-white">Join Existing Company</span>
              <span className="mt-1 block text-sm text-slate-400">
                Accept an invitation to join a company that already exists.
              </span>
            </span>
            <span className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-cyan-400 group-hover:text-cyan-300">
              Join now <ArrowRight size={16} />
            </span>
          </Link>
        </div>
      </div>
    </main>
  )
}
