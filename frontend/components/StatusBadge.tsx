"use client"

export type StatusVariant = 'progress' | 'ontrack' | 'risk' | 'completed' | 'paused' | 'default'

interface StatusBadgeProps {
  status: string
  variant?: StatusVariant
  className?: string
}

/** Static full class strings so Tailwind can detect them. */
const VARIANTS: Record<StatusVariant, string> = {
  progress: 'bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-300',
  ontrack: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300',
  risk: 'bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-300',
  completed: 'bg-brand-50 text-brand-700 dark:bg-brand-600/10 dark:text-brand-300',
  paused: 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300',
  default: 'bg-slate-100 text-slate-700 dark:bg-slate-700/40 dark:text-slate-300',
}

const DOTS: Record<StatusVariant, string> = {
  progress: 'bg-blue-500',
  ontrack: 'bg-emerald-500',
  risk: 'bg-red-500',
  completed: 'bg-brand-600',
  paused: 'bg-amber-500',
  default: 'bg-slate-400',
}

/**
 * Reusable AI-BOS status badge (e.g. In Progress, On Track, At Risk).
 */
export default function StatusBadge({
  status,
  variant = 'default',
  className = '',
}: StatusBadgeProps) {
  return (
    <span
      className={[
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
        VARIANTS[variant],
        className,
      ].join(' ')}
    >
      <span className={['h-1.5 w-1.5 rounded-full', DOTS[variant]].join(' ')} />
      {status}
    </span>
  )
}
