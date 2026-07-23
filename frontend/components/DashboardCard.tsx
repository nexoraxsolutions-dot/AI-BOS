interface DashboardCardProps {
  title: string
  value: string
  description: string
}

export default function DashboardCard({ title, value, description }: DashboardCardProps) {
  return (
    <div className="rounded-3xl border border-white/10 bg-slate-950/50 p-6 shadow-xl backdrop-blur-xl">
      <p className="text-sm font-medium text-cyan-300">{title}</p>
      <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
      <p className="mt-1 text-sm text-slate-400">{description}</p>
    </div>
  )
}