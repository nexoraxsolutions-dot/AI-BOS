"use client"

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  Sparkles,
  ChevronDown,
  Paperclip,
  Mic,
  Send,
  FileText,
  Database,
  Receipt,
  Bot,
} from 'lucide-react'

interface AIAssistantDrawerProps {
  open: boolean
  onClose: () => void
}

const AGENTS = [
  { id: 'finance', name: 'AI Finance Manager', icon: Database },
  { id: 'sales', name: 'AI Sales Manager', icon: Receipt },
  { id: 'ceo', name: 'AI CEO', icon: Bot },
]

const CITATIONS = [
  { label: 'Finance Database', icon: Database },
  { label: 'Invoice Module', icon: Receipt },
  { label: 'Aged Receivables Report', icon: FileText },
]

const ACTION_CHIPS = ['Show by customer', 'Download report', 'Compare Q3 vs Q4', 'Forecast next month']

interface Message {
  role: 'user' | 'assistant'
  text: string
}

const INITIAL_MESSAGES: Message[] = [
  {
    role: 'assistant',
    text: "Hi! I'm your AI Finance Manager. Revenue is up by 12.5% this month. Aged receivables dropped 8%. What would you like to explore?",
  },
  {
    role: 'user',
    text: 'Give me a breakdown of revenue by source.',
  },
  {
    role: 'assistant',
    text: 'Direct drives 45% of revenue ($1.26M), Referral 25%, Social Media 15%, and Others 15%. Direct is your strongest channel — up 18% MoM.',
  },
]

export default function AIAssistantDrawer({ open, onClose }: AIAssistantDrawerProps) {
  const [agentId, setAgentId] = useState('finance')
  const [agentOpen, setAgentOpen] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES)

  const activeAgent = AGENTS.find((a) => a.id === agentId) ?? AGENTS[0]

  const send = () => {
    const text = input.trim()
    if (!text) return
    setInput('')
    setMessages((prev) => [
      ...prev,
      { role: 'user', text },
      {
        role: 'assistant',
        text: 'Based on the cited sources, here is a summary of the latest figures. You can download the full report below.',
      },
    ])
  }

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm"
          />

          {/* Slide-over panel */}
          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', stiffness: 320, damping: 34 }}
            className="fixed right-0 top-0 z-50 flex h-screen w-full max-w-md flex-col border-l border-slate-200 bg-white shadow-2xl dark:border-dark-border dark:bg-dark-surface"
          >
            {/* Header: Agent selector */}
            <div className="flex items-center justify-between border-b border-slate-200 p-4 dark:border-dark-border">
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-glow">
                  <Sparkles size={18} />
                </div>
                <div className="relative">
                  <button
                    onClick={() => setAgentOpen((v) => !v)}
                    className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-sm font-semibold text-slate-900 hover:bg-slate-100 dark:text-dark-text dark:hover:bg-white/5"
                  >
                    {activeAgent.name}
                    <ChevronDown size={14} className={agentOpen ? 'rotate-180 transition' : 'transition'} />
                  </button>
                  <AnimatePresence>
                    {agentOpen && (
                      <motion.ul
                        initial={{ opacity: 0, y: -6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -6 }}
                        className="absolute left-0 top-full z-10 mt-1 w-56 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-cardLg dark:border-dark-border dark:bg-dark-surface"
                      >
                        {AGENTS.map((a) => {
                          const Icon = a.icon
                          return (
                            <li key={a.id}>
                              <button
                                onClick={() => {
                                  setAgentId(a.id)
                                  setAgentOpen(false)
                                }}
                                className={[
                                  'flex w-full items-center gap-2 px-3 py-2 text-sm transition',
                                  a.id === agentId
                                    ? 'bg-brand-50 text-brand-700 dark:bg-brand-600/10 dark:text-brand-300'
                                    : 'text-slate-600 hover:bg-slate-100 dark:text-dark-muted dark:hover:bg-white/5',
                                ].join(' ')}
                              >
                                <Icon size={16} />
                                {a.name}
                              </button>
                            </li>
                          )
                        })}
                      </motion.ul>
                    )}
                  </AnimatePresence>
                </div>
              </div>
              <button
                onClick={onClose}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-white/5 dark:hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            {/* Citation / source panel */}
            <div className="border-b border-slate-200 p-4 dark:border-dark-border">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-dark-muted">
                Cited Sources
              </p>
              <div className="grid grid-cols-1 gap-2">
                {CITATIONS.map((c) => {
                  const Icon = c.icon
                  return (
                    <div
                      key={c.label}
                      className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-dark-border dark:bg-white/5"
                    >
                      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-600/10 dark:text-brand-300">
                        <Icon size={14} />
                      </span>
                      <span className="font-medium text-slate-700 dark:text-dark-text">{c.label}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Chat interface */}
            <div className="flex-1 space-y-4 overflow-y-auto p-4 scrollbar-thin">
              {messages.map((m, i) =>
                m.role === 'user' ? (
                  <div key={i} className="flex justify-end">
                    <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-brand-600 px-3.5 py-2 text-sm text-white shadow-sm">
                      {m.text}
                    </div>
                  </div>
                ) : (
                  <div key={i} className="flex items-start gap-2.5">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-gradient text-white">
                      <Sparkles size={14} />
                    </div>
                    <div className="max-w-[80%] rounded-2xl rounded-bl-sm border border-slate-200 bg-slate-50 px-3.5 py-2 text-sm text-slate-700 dark:border-dark-border dark:bg-white/5 dark:text-dark-text">
                      {m.text}
                    </div>
                  </div>
                )
              )}

              {/* Action chips */}
              <div className="flex flex-wrap gap-2 pt-1">
                {ACTION_CHIPS.map((chip) => (
                  <button
                    key={chip}
                    onClick={() => setInput(chip)}
                    className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 transition hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700 dark:border-dark-border dark:bg-white/5 dark:text-dark-muted dark:hover:border-brand-500/40 dark:hover:bg-brand-600/10 dark:hover:text-brand-300"
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>

            {/* Fixed input bar */}
            <div className="border-t border-slate-200 p-3 dark:border-dark-border">
              <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-dark-border dark:bg-white/5">
                <button
                  className="text-slate-400 hover:text-brand-600 dark:hover:text-brand-300"
                  aria-label="Attach file"
                >
                  <Paperclip size={18} />
                </button>
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && send()}
                  placeholder="Ask the AI assistant..."
                  className="flex-1 bg-transparent text-sm text-slate-700 placeholder-slate-400 focus:outline-none dark:text-dark-text dark:placeholder-dark-muted"
                />
                <button
                  className="text-slate-400 hover:text-brand-600 dark:hover:text-brand-300"
                  aria-label="Voice input"
                >
                  <Mic size={18} />
                </button>
                <button
                  onClick={send}
                  className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white transition hover:bg-brand-700 active:scale-95"
                  aria-label="Send"
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}

