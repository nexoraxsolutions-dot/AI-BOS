import LoginForm from '../components/LoginForm'
import DashboardCard from '../components/DashboardCard'

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-white py-12 px-6">
      <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[1.2fr_0.8fr]">
        <section className="space-y-8 rounded-[2rem] border border-white/10 bg-white/5 p-10 shadow-2xl backdrop-blur-xl">
          <div className="space-y-3">
            <p className="text-cyan-300 uppercase tracking-[0.3em] text-sm">AI-BOS</p>
            <h1 className="text-5xl font-semibold">Enterprise AI Business Operating System</h1>
            <p className="max-w-2xl text-slate-300">Secure access for company admins and teams, with centralized user, company, and dashboard management.</p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <DashboardCard title="Companies" value="12" description="Active tenant organizations" />
            <DashboardCard title="Users" value="248" description="Platform users and collaborators" />
            <DashboardCard title="Sales" value="$1.8M" description="Revenue tracked this month" />
            <DashboardCard title="Tasks" value="84" description="Projects in progress" />
          </div>
        </section>

        <aside className="rounded-[2rem] border border-white/10 bg-slate-950/90 p-10 shadow-2xl backdrop-blur-xl">
          <h2 className="text-3xl font-semibold text-white">Sign in</h2>
          <p className="mt-2 text-slate-400">Log in securely using your company credentials.</p>
          <LoginForm />
        </aside>
      </div>
    </main>
  )
}
