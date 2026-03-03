'use client'

import { ExternalLink } from 'lucide-react'
import { GlassCard } from '@/components/ui/glass-card'

const sections = [
  {
    title: 'Data Collection',
    content: (
      <div className="space-y-3 text-sm text-[var(--text-secondary)]">
        <p>All data collected from <strong className="text-[var(--text-primary)]">GitHub API</strong> (public repositories only). Period: January 2025 - February 2026.</p>
        <p>Repositories included if they had at least one commit, PR, or Co-Author tag with detected AI agent attribution.</p>
      </div>
    ),
  },
  {
    title: 'Agent Detection',
    content: (
      <div className="space-y-2 text-sm text-[var(--text-secondary)]">
        <p><strong className="text-purple-400">Claude Code:</strong> Co-Author tags from Anthropic</p>
        <p><strong className="text-blue-400">Copilot:</strong> PR metadata and commit patterns matching Copilot signatures</p>
        <p><strong className="text-green-400">Codex:</strong> Commits/PRs with Codex API attribution</p>
        <p><strong className="text-orange-400">Cursor AI:</strong> Branch naming (cursor/) and Co-Author tags</p>
        <p className="mt-2">Validation (1,000 samples per agent): Claude 94.2% TPR, Copilot 91.8%, Codex 89.5%</p>
      </div>
    ),
  },
  {
    title: 'Industry Classification Model',
    content: (
      <div className="space-y-2 text-sm text-[var(--text-secondary)]">
        <p>Fine-tuned <strong className="text-[var(--text-primary)]">RoBERTa-base</strong> trained on 50,000 manually labeled repository-to-industry mappings.</p>
        <p>Input: repository description + topics + README excerpt (512 tokens). Output: 20 NAICS sector codes.</p>
        <p>Performance: <strong className="text-green-400">Accuracy 78.3%</strong>, Macro F1 0.72, Weighted F1 0.79</p>
        <p>Best sectors: Professional Services (F1: 0.87), Information (F1: 0.80), Finance (F1: 0.76)</p>
      </div>
    ),
  },
  {
    title: 'Confidence Calibration',
    content: (
      <div className="space-y-2 text-sm text-[var(--text-secondary)]">
        <p>Calibrated using isotonic regression on 2,000 manually verified predictions.</p>
        <p>At threshold &gt;0.7: 72% coverage, 82% accuracy. At &gt;0.9: 35% coverage, 94% accuracy.</p>
        <p className="text-[var(--text-muted)] italic">Visualizations include all predictions without confidence filtering to maximize coverage.</p>
      </div>
    ),
  },
  {
    title: 'Limitations',
    content: (
      <div className="space-y-2 text-sm text-[var(--text-secondary)]">
        <ul className="list-disc list-inside space-y-1">
          <li><strong className="text-[var(--text-primary)]">Public repos only</strong> — enterprise/private usage not captured</li>
          <li><strong className="text-[var(--text-primary)]">GitHub only</strong> — GitLab, Bitbucket not included</li>
          <li><strong className="text-[var(--text-primary)]">Detection gaps</strong> — implicit usage without attribution missed (15-25% false negative rate)</li>
          <li><strong className="text-[var(--text-primary)]">Repo-level classification</strong> — not organization-level</li>
          <li><strong className="text-[var(--text-primary)]">Adoption vs. usage</strong> — captures first-use date, not intensity</li>
        </ul>
        <p className="mt-2 text-amber-400/80 text-xs">Trend analysis within a single agent is more reliable than cross-agent absolute comparisons.</p>
      </div>
    ),
  },
]

export function MethodologySection() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">Methodology</h2>
        <p className="text-[var(--text-secondary)]">How we collect, process, and analyze AI coding agent adoption data</p>
      </div>

      <GlassCard className="space-y-0 divide-y divide-[var(--border)]">
        {sections.map((section) => (
          <details key={section.title} className="group">
            <summary className="flex items-center justify-between cursor-pointer px-2 py-4 text-[var(--text-primary)] font-semibold hover:text-purple-400 transition-colors">
              <span>{section.title}</span>
              <span className="text-[var(--text-muted)] text-xs group-open:rotate-180 transition-transform">
                &#9660;
              </span>
            </summary>
            <div className="pb-4 px-2">
              {section.content}
            </div>
          </details>
        ))}
      </GlassCard>

      <div className="mt-4 flex items-center justify-between text-sm">
        <div className="flex gap-6 text-[var(--text-muted)]">
          <span>Next.js 16</span>
          <span>Supabase</span>
          <span>Recharts</span>
          <span>RoBERTa</span>
        </div>
        <a
          href="https://github.com/raulsedano2410/ai-coding-agents-next"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-purple-400 hover:text-purple-300 transition-colors"
        >
          Source code
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>
    </div>
  )
}
