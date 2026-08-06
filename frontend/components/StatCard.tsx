"use client"

import { motion } from 'framer-motion'
import { ArrowUp, ArrowDown } from 'lucide-react'

type Accent = 'brand' | 'emerald' | 'blue' | 'amber' | 'rose' | 'violet'

/** Static full class strings (Tailwind needs literal names to detect them). */
const ACCENTS: Record<Accent, { bg: string; text: string }> = {
  brand: { bg: 'bg-brand-600/10', text: 'text-brand-600' },
  violet: { bg: 'bg-brand-500/10', text: 'text-brand-500' },
  emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-600' },
  blue: { bg: 'bg-blue-500/10', text: 'text-blue-600' },
  amber: { bg: 'bg-amber-500/10', text: 'text-amber-600' },
  rose: { bg: 'bg-rose-500/10', text: 'text-rose-600' },
}

interface StatCardProps {
  label: string
  value: string
  icon: React.ReactNode
  accent?: Accent
  trend?: {
    value: string
    direction: 'up' | 'down'
    label?: string
  }
  className?: string
}

/**
 * Reusable AI-BOS metric card.
 * Layout: circular colored icon container (left), value on top,
 * percentage trend indicator at the bottom (green ↑ / red ↓).
 */
export default function StatCard({
  label,
  value,
  icon,
  accent = 'brand',
  trend,
  className = '',
}: StatCardProps) {
  const isUp = trend?.direction === 'up'
  const accentClasses = ACCENTS[accent]

  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      className={['card flex items-start justify-between p-5', className].join(' ')}
    >
      <div className="min-w-0">
        <p className="text-sm font-medium text-slate-500 dark:text-dark-muted">{label}</p>
        <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 dark:text-dark-text">
          {value}
        </p>
        {trend && (
          <div className="mt-2 flex items-center gap-1 text-xs font-medium">
            <span
              className={[
                'inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5',
                isUp
                  ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400'
                  : 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400',
              ].join(' ')}
            >
              {isUp ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
              {trend.value}
            </span>
            {trend.label && (
              <span className="text-slate-400 dark:text-dark-muted">{trend.label}</span>
            )}
          </div>
        )}
      </div>

      {/* Circular colored icon container */}
      <div
        className={[
          'flex h-11 w-11 shrink-0 items-center justify-center rounded-full',
          accentClasses.bg,
          accentClasses.text,
        ].join(' ')}
      >
        {icon}
      </div>
    </motion.div>
  )
}

