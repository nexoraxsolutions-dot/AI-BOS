"use client"

import { useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import SidebarItem from './SidebarItem'
import AIAssistantDrawer from './AIAssistantDrawer'
import {
  LayoutDashboard,
  Users,
  Building2,
  Briefcase,
  Shield,
  Settings,
  User,
  LogOut,
  Search,
  Bell,
  Sparkles,
  ChevronDown,
  ChevronRight,
  Server,
  Key,
  Lock,
  FileText,
  Eye,
  Database,
  Container,
  PanelLeftClose,
  PanelLeftOpen,
  FlaskConical,
  BookOpen,
  SlidersHorizontal,
  Sun,
  Moon,
  Plus,
  Calendar,
  MessageSquare,
  Menu,
  X,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface NavSection {
  title: string
  items: NavItem[]
  collapsible?: boolean
  defaultCollapsed?: boolean
}

interface NavItem {
  label: string
  href: string
  icon: React.ReactNode
}

export default function Sidebar({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const { isAuthenticated, logout, user } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [aiOpen, setAiOpen] = useState(false)
  const [sections, setSections] = useState<Record<string, boolean>>({
    MAIN: false,
    WORKSPACE: false,
    ORGANIZATION: false,
    SECURITY: false,
    SYSTEM: true, // Collapsed by default
  })

  if (!isAuthenticated) {
    return null
  }

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  const toggleSection = (section: string) => {
    setSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const navSections: NavSection[] = [
    {
      title: 'MAIN',
      items: [
        {
          label: 'Dashboard',
          href: '/dashboard',
          icon: <LayoutDashboard size={20} />,
        },
      ],
    },
    {
      title: 'WORKSPACE',
      items: [
        {
          label: 'Users',
          href: '/users',
          icon: <Users size={20} />,
        },
        {
          label: 'Departments',
          href: '/departments',
          icon: <Briefcase size={20} />,
        },
        {
          label: 'Companies',
          href: '/companies',
          icon: <Building2 size={20} />,
        },
      ],
    },
    {
      title: 'ORGANIZATION',
      items: [
        {
          label: 'Roles',
          href: '/roles',
          icon: <Shield size={20} />,
        },
        {
          label: 'Organization Settings',
          href: '/organization-settings',
          icon: <Settings size={20} />,
        },
        {
          label: 'Profile',
          href: '/profile',
          icon: <User size={20} />,
        },
      ],
    },
    {
      title: 'SECURITY',
      items: [
        {
          label: 'Security Dashboard',
          href: '/security',
          icon: <Shield size={20} />,
        },
        {
          label: 'Sessions',
          href: '/sessions',
          icon: <Eye size={20} />,
        },
        {
          label: 'API Keys',
          href: '/api-keys',
          icon: <Key size={20} />,
        },
        {
          label: 'Password Policy',
          href: '/password-policy',
          icon: <Lock size={20} />,
        },
        {
          label: 'Audit Logs',
          href: '/audit-logs',
          icon: <FileText size={20} />,
        },
      ],
    },
    {
      title: 'SYSTEM',
      collapsible: true,
      defaultCollapsed: true,
      items: [
        {
          label: 'Environment Variables',
          href: '/environment-variables',
          icon: <Server size={20} />,
        },
        {
          label: 'Redis',
          href: '/redis',
          icon: <Database size={20} />,
        },
        {
          label: 'Tokens',
          href: '/tokens',
          icon: <Key size={20} />,
        },
        {
          label: 'Tenants',
          href: '/tenants',
          icon: <Container size={20} />,
        },
        {
          label: 'Test Framework',
          href: '/test-framework',
          icon: <FlaskConical size={20} />,
        },
        {
          label: 'Logging',
          href: '/logging',
          icon: <FileText size={20} />,
        },
        {
          label: 'Logging Configuration',
          href: '/logging-configuration',
          icon: <SlidersHorizontal size={20} />,
        },
        {
          label: 'Documentation',
          href: '/documentation',
          icon: <BookOpen size={20} />,
        },
      ],
    },
  ]

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard'
    }
    return pathname.startsWith(href)
  }

  return (
    <>
      {/* Sidebar */}
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm md:hidden"
        />
      )}

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: isCollapsed ? 80 : 280 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className={[
          'fixed left-0 top-0 z-50 h-screen flex flex-col border-r border-white/10 bg-sidebar text-white',
          'transition-transform duration-300',
          mobileOpen ? 'translate-x-0' : '-translate-x-full',
          'md:translate-x-0',
        ].join(' ')}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b border-white/10 px-4">
          {!isCollapsed ? (
            <button
              onClick={() => {
                router.push('/dashboard')
                setMobileOpen(false)
              }}
              className="flex items-center gap-2"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient shadow-glow">
                <Sparkles className="text-white" size={18} />
              </span>
              <span className="text-gradient text-lg font-bold">AI-BOS</span>
            </button>
          ) : (
            <div className="flex w-full justify-center">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient shadow-glow">
                <Sparkles className="text-white" size={18} />
              </span>
            </div>
          )}
          <button
            onClick={() => setMobileOpen(false)}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-white/5 hover:text-white md:hidden"
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden rounded-lg p-2 text-slate-400 transition hover:bg-white/5 hover:text-white md:block"
            aria-label="Toggle sidebar"
          >
            {isCollapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}
          </button>
        </div>

        {/* Navigation Sections */}
        <div className="flex-1 overflow-y-auto py-4 px-3 space-y-6 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
          {navSections.map((section) => (
            <div key={section.title}>
              {!isCollapsed && (
                <div className="flex items-center justify-between px-3 mb-2">
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    {section.title}
                  </h3>
                  {section.collapsible && (
                    <button
                      onClick={() => toggleSection(section.title)}
                      className="p-1 rounded hover:bg-white/5 transition text-slate-500 hover:text-slate-300"
                    >
                      {sections[section.title] ? (
                        <ChevronDown size={14} />
                      ) : (
                        <ChevronRight size={14} />
                      )}
                    </button>
                  )}
                </div>
              )}
              {isCollapsed && section.collapsible && (
                <div className="flex justify-center mb-2">
                  <button
                    onClick={() => toggleSection(section.title)}
                    className="p-1 rounded hover:bg-white/5 transition text-slate-500 hover:text-slate-300"
                  >
                    {sections[section.title] ? (
                      <ChevronDown size={14} />
                    ) : (
                      <ChevronRight size={14} />
                    )}
                  </button>
                </div>
              )}

              <AnimatePresence initial={false}>
                {(sections[section.title] !== false || !section.collapsible) && (
                  <motion.div
                    initial={section.collapsible ? { height: 0, opacity: 0 } : false}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="space-y-1"
                  >
                    {section.items.map((item) => {
                      const active = isActive(item.href)
                      return (
                        <SidebarItem
                          key={item.href}
                          label={item.label}
                          icon={item.icon}
                          href={item.href}
                          active={active}
                          collapsed={isCollapsed}
                          onClick={() => {
                            router.push(item.href)
                            setMobileOpen(false)
                          }}
                        />
                      )
                    })}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>

        {/* User Profile & Logout */}
        <div className="border-t border-white/10 p-3">
          {!isCollapsed && user && (
            <div className="mb-3 flex items-center gap-3 rounded-xl bg-white/5 px-3 py-2.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-gradient text-sm font-semibold text-white">
                {user.full_name?.[0] || user.username?.[0] || user.email[0].toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-white">
                  {user.full_name || user.username || 'User'}
                </p>
                <p className="truncate text-xs text-slate-400">{user.email}</p>
              </div>
              <button
                onClick={toggleTheme}
                className="rounded-lg p-1.5 text-slate-400 transition hover:bg-white/10 hover:text-amber-300"
                aria-label="Toggle theme"
              >
                {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
              </button>
            </div>
          )}
          {isCollapsed && user && (
            <div className="mb-3 flex justify-center">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-gradient text-sm font-semibold text-white">
                {user.full_name?.[0] || user.username?.[0] || user.email[0].toUpperCase()}
              </div>
            </div>
          )}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleLogout}
            className={`
              w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
              text-slate-400 hover:text-red-400 hover:bg-red-500/10
              ${isCollapsed ? 'justify-center' : ''}
            `}
          >
            <LogOut size={20} />
            {!isCollapsed && <span className="text-sm font-medium">Sign Out</span>}
          </motion.button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <div
        className={[
          'min-h-screen bg-slate-50 transition-[padding] duration-300 dark:bg-dark-bg',
          isCollapsed ? 'md:pl-20' : 'md:pl-72',
        ].join(' ')}
      >
        {/* Top Header */}
        <header className="sticky top-0 z-30 h-16 border-b border-slate-200 bg-white/80 backdrop-blur-xl dark:border-dark-border dark:bg-dark-surface/80">
          <div className="flex h-full items-center justify-between gap-4 px-4 md:px-6">
            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileOpen(true)}
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 md:hidden dark:hover:bg-white/5"
              aria-label="Open menu"
            >
              <Menu size={20} />
            </button>

            {/* Universal Search */}
            <div className="flex flex-1 items-center">
              <div className="relative w-full max-w-xl">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  type="text"
                  placeholder="Search anything... (Cmd+K)"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pl-10 pr-4 text-sm text-slate-700 placeholder-slate-400 focus:border-brand-400 focus:bg-white focus:outline-none dark:border-dark-border dark:bg-white/5 dark:text-dark-text"
                />
              </div>
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-2 md:gap-3">
              {/* Quick Action */}
              <button className="hidden items-center gap-1.5 rounded-xl bg-brand-600 px-3.5 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-brand-700 sm:flex">
                <Plus size={16} /> Quick Action
              </button>

              {/* Calendar */}
              <button
                className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5"
                aria-label="Calendar"
              >
                <Calendar size={20} />
              </button>

              {/* Chat toggle */}
              <button
                onClick={() => setAiOpen(true)}
                className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5"
                aria-label="Chat"
              >
                <MessageSquare size={20} />
              </button>

              {/* Notifications with counter */}
              <button
                className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5"
                aria-label="Notifications"
              >
                <Bell size={20} />
                <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-brand-600 text-[10px] font-semibold text-white">
                  3
                </span>
              </button>

              {/* AI Assistant trigger */}
              <button
                onClick={() => setAiOpen(true)}
                className="flex items-center gap-1.5 rounded-xl bg-brand-600 px-3 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-brand-700"
              >
                <Sparkles size={16} />
                <span className="hidden sm:inline">AI Assistant</span>
              </button>

              {/* Profile dropdown — Acme Corp */}
              <button className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white py-1.5 pl-1.5 pr-2.5 text-sm hover:bg-slate-50 dark:border-dark-border dark:bg-white/5 dark:hover:bg-white/10">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-gradient text-xs font-semibold text-white">
                  A
                </div>
                <span className="hidden font-medium text-slate-700 sm:inline dark:text-dark-text">Acme Corp</span>
                <ChevronDown size={14} className="text-slate-400" />
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 md:p-6">{children}</main>
      </div>

      {/* AI Assistant slide-over drawer */}
      <AIAssistantDrawer open={aiOpen} onClose={() => setAiOpen(false)} />
    </>
  )
}