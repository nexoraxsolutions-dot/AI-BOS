import Link from 'next/link'
import { Sparkles, ArrowRight } from 'lucide-react'
import DashboardCard from '../components/DashboardCard'

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 px-6 py-12 dark:bg-dark-bg">
      <div className="mx-auto max-w-6xl">
        <section className="space-y-8 rounded-[2rem] border border-slate-200 bg-white p-8 shadow-cardLg sm:p-12 dark:border-dark-border dark:bg-dark-surface">
          <div className="space-y-3 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-brand-gradient shadow-glow">
              <Sparkles className="text-white" size={24} />
            </div>
            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-brand-600">AI-BOS</p>
            <h1 className="text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl dark:text-dark-text">
              <span className="text-gradient">Enterprise AI</span> Business Operating System
            </h1>
            <p className="mx-auto max-w-2xl text-slate-500 dark:text-dark-muted">
              Secure access for company admins and teams, with centralized user, company, and dashboard management.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <DashboardCard title="Companies" value="12" description="Active tenant organizations" />
            <DashboardCard title="Users" value="248" description="Platform users and collaborators" />
            <DashboardCard title="Sales" value="$1.8M" description="Revenue tracked this month" />
            <DashboardCard title="Tasks" value="84" description="Projects in progress" />
          </div>

          <div className="flex flex-wrap justify-center gap-4 pt-2">
            <Link href="/login" className="btn-brand">
              Sign in <ArrowRight size={16} />
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-8 py-2.5 text-base font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-dark-border dark:bg-white/5 dark:text-dark-text dark:hover:bg-white/10"
            >
              Create account
            </Link>
          </div>
        </section>
      </div>
    </main>
  )
}