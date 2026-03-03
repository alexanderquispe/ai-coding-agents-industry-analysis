'use client'

import { useTheme } from '@/lib/theme-context'
import { Sun, Moon, Monitor } from 'lucide-react'

const themeOrder = ['dark', 'light', 'system'] as const

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const next = () => {
    const idx = themeOrder.indexOf(theme)
    setTheme(themeOrder[(idx + 1) % themeOrder.length])
  }

  return (
    <button
      onClick={next}
      className="rounded-lg p-2 text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)] transition-colors"
      title={`Theme: ${theme}`}
    >
      {theme === 'dark' && <Moon className="h-4 w-4" />}
      {theme === 'light' && <Sun className="h-4 w-4" />}
      {theme === 'system' && <Monitor className="h-4 w-4" />}
    </button>
  )
}
