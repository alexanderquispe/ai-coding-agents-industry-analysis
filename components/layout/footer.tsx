import Link from 'next/link'
import { Github, ExternalLink } from 'lucide-react'

export function Footer() {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--bg-primary)]">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
          <div className="flex flex-col items-center gap-2 md:items-start">
            <p className="text-sm text-[var(--text-secondary)]">
              AI Coding Agents Industry Analysis
            </p>
            <p className="text-xs text-[var(--text-muted)]">
              Data sourced from GitHub public repositories
            </p>
          </div>

          <div className="flex items-center gap-4">
            <Link
              href="/methodology"
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              Methodology
            </Link>
            <a
              href="https://github.com/alexanderquispe"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              <Github className="h-4 w-4" />
              <span>GitHub</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>

        <div className="mt-6 border-t border-[var(--border)] pt-6 text-center">
          <p className="text-xs text-[var(--text-muted)]">
            Built with Next.js, Supabase, and Recharts. Classification powered by NAICS codes.
          </p>
        </div>
      </div>
    </footer>
  )
}
