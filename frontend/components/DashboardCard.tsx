interface DashboardCardProps {
  title: string
  value: string
  description: string
}

export default function DashboardCard({ title, value, description }: DashboardCardProps) {
  return (
    <div className="card p-6">
      <p className="text-sm font-medium text-brand-600">{title}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-900 dark:text-dark-text">{value}</p>
      <p className="mt-1 text-sm text-slate-500 dark:text-dark-muted">{description}</p>
    </div>
  )
}