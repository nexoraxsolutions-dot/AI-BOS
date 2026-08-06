"use client"

import { motion } from 'framer-motion'

interface SidebarItemProps {
  label: string
  icon: React.ReactNode
  href: string
  active: boolean
  collapsed?: boolean
  onClick: () => void
}

/**
 * Reusable AI-BOS sidebar navigation item.
 * - Active: fully filled bright violet pill (bg-brand-700) with white text + shadow.
 * - Inactive: muted slate text, hover transitions toward white with subtle bg.
 */
export default function SidebarItem({
  label,
  icon,
  active,
  collapsed = false,
  onClick,
}: SidebarItemProps) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={[
        'group relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200',
        collapsed ? 'justify-center' : '',
        active
          ? 'bg-gradient-to-r from-brand-600 to-brand-700 text-white shadow-active'
          : 'text-slate-400 hover:bg-white/5 hover:text-white',
      ].join(' ')}
    >
      <span
        className={[
          'flex h-5 w-5 items-center justify-center',
          active ? 'text-white' : 'text-slate-500 group-hover:text-slate-200',
        ].join(' ')}
      >
        {icon}
      </span>

      {!collapsed && <span className="truncate">{label}</span>}

      {/* Tooltip when collapsed */}
      {collapsed && (
        <span className="pointer-events-none absolute left-full ml-2 z-50 whitespace-nowrap rounded-lg border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-white opacity-0 transition group-hover:opacity-100">
          {label}
        </span>
      )}
    </motion.button>
  )
}
