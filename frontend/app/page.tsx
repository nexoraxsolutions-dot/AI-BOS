import Link from 'next/link'
import DashboardCard from '../components/DashboardCard'

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto max-w-6xl">
        <section className="space-y-8 rounded-[2rem] border border-white/10 bg-white/5 p-10 shadow-2xl backdrop-blur-xl">
          <div className="space-y-3 text-center">
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="text-5xl font-semibold">Enterprise AI Business Operating System</h1>
            <p className="max-w-2xl mx-auto text-slate-300">Secure access for company admins and teams, with centralized user, company, and dashboard management.</p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <DashboardCard title="Companies" value="12" description="Active tenant organizations" />
            <DashboardCard title="Users" value="248" description="Platform users and collaborators" />
            <DashboardCard title="Sales" value="$1.8M" description="Revenue tracked this month" />
            <DashboardCard title="Tasks" value="84" description="Projects in progress" />
          </div>

          <div className="flex justify-center gap-4 pt-4">
            <Link
              href="/login"
              className="rounded-2xl bg-cyan-500 px-8 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400"
            >
              Sign in
            </Link>
            <Link
              href="/register"
              className="rounded-2xl border border-white/10 bg-white/5 px-8 py-3 text-base font-semibold text-white transition hover:bg-white/10"
            >
              Create account
            </Link>
          </div>
        </section>
      </div>
    </main>
  )
}