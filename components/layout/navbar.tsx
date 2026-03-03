'use client'

import { useState, useEffect } from 'react'
import { BarChart3, Menu, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ThemeToggle } from '@/components/ui/theme-toggle'

const navSections = [
  { id: 'hero', label: 'Overview' },
  { id: 'comparison', label: 'Comparison' },
  { id: 'industries', label: 'Industries' },
  { id: 'trends', label: 'Trends' },
  { id: 'findings', label: 'Findings' },
  { id: 'methodology', label: 'Methodology' },
]

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false)
  const [activeSection, setActiveSection] = useState('hero')

  useEffect(() => {
    const observers: IntersectionObserver[] = []
    navSections.forEach(({ id }) => {
      const el = document.getElementById(id)
      if (!el) return
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) setActiveSection(id)
        },
        { rootMargin: '-30% 0px -60% 0px' }
      )
      observer.observe(el)
      observers.push(observer)
    })
    return () => observers.forEach(o => o.disconnect())
  }, [])

  const scrollTo = (id: string) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setIsOpen(false)
    }
  }

  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--bg-primary)]/80 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <button onClick={() => scrollTo('hero')} className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-purple-500" />
            <span className="text-lg font-semibold text-[var(--text-primary)]">
              AI Coding Agents
            </span>
          </button>

          {/* Desktop Navigation */}
          <div className="hidden md:flex md:items-center md:gap-1">
            {navSections.map((section) => (
              <button
                key={section.id}
                onClick={() => scrollTo(section.id)}
                className={cn(
                  'relative rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  activeSection === section.id
                    ? 'text-[var(--text-primary)]'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                )}
              >
                {section.label}
                {activeSection === section.id && (
                  <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4/5 h-0.5 bg-purple-500 rounded-full" />
                )}
              </button>
            ))}
            <ThemeToggle />
          </div>

          {/* Mobile: theme toggle + menu button */}
          <div className="flex items-center gap-1 md:hidden">
            <ThemeToggle />
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="rounded-lg p-2 text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]"
            >
              {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isOpen && (
        <div className="md:hidden border-t border-[var(--border)] bg-[var(--bg-primary)]/95 backdrop-blur-md">
          <div className="space-y-1 px-4 py-3">
            {navSections.map((section) => (
              <button
                key={section.id}
                onClick={() => scrollTo(section.id)}
                className={cn(
                  'block w-full text-left rounded-lg px-3 py-2 text-base font-medium transition-colors',
                  activeSection === section.id
                    ? 'bg-[var(--bg-tertiary)] text-[var(--text-primary)]'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]/50 hover:text-[var(--text-primary)]'
                )}
              >
                {section.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </nav>
  )
}
