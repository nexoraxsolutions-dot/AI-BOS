"use client"

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextType>({
  theme: 'light',
  toggleTheme: () => {},
  setTheme: () => {},
})

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('light')
  const [mounted, setMounted] = useState(false)

  // Read persisted / system preference on mount
  useEffect(() => {
    const stored = localStorage.getItem('ai_bos_theme') as Theme | null
    if (stored === 'light' || stored === 'dark') {
      setThemeState(stored)
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setThemeState('dark')
    }
    setMounted(true)
  }, [])

  // Reflect theme onto <html> and persist
  useEffect(() => {
    if (!mounted) return
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem('ai_bos_theme', theme)
  }, [theme, mounted])

  const setTheme = (next: Theme) => setThemeState(next)
  const toggleTheme = () => setThemeState((prev) => (prev === 'dark' ? 'light' : 'dark'))

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}
