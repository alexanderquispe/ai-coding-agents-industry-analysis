'use client'

import { useState } from 'react'
import { useAgentSelection } from '@/lib/agent-context'
import { INDUSTRIES, AGENT_COMPANIES, AGENT_STATS } from '@/lib/constants'
import { formatNumber } from '@/lib/utils'
import { Agent } from '@/lib/types'
import { ProcessedAgentData } from '@/lib/data-processing'
import { Download } from 'lucide-react'

interface HeroSectionProps {
  agents: Agent[]
  allAgentStats: Record<string, ProcessedAgentData>
  monthRange: string
}

export function HeroSection({ agents, allAgentStats, monthRange }: HeroSectionProps) {
  const { selectedAgent } = useAgentSelection()
  const [downloading, setDownloading] = useState(false)

  async function downloadAllData() {
    setDownloading(true)
    try {
      const basePath = '/ai-coding-agents-industry-analysis'
      const agentIds = ['claude', 'copilot', 'codex', 'cursor']
      const responses = await Promise.all(
        agentIds.map(id => fetch(`${basePath}/data/${id}_cumulative.json`).then(r => r.json()))
      )

      const rows: string[] = ['month,agent,industry_code,industry_name,cumulative,new_repos']
      agentIds.forEach((agentId, ai) => {
        const data = responses[ai]
        const months: string[] = data.months
        for (const industry of data.industries) {
          const code = industry.code
          const name = industry.name.replace(/^\d[\d-]*:\s*/, '')
          months.forEach((month: string, mi: number) => {
            const cumulative = industry.values[mi] ?? 0
            const newRepos = industry.monthly[mi] ?? 0
            rows.push(`${month},${agentId},${code},"${name}",${cumulative},${newRepos}`)
          })
        }
      })

      const blob = new Blob([rows.join('\n')], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'ai-coding-agents-data.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error('Download failed:', e)
    } finally {
      setDownloading(false)
    }
  }

  if (selectedAgent === 'all') {
    const totalRepos = agents.reduce((sum, a) => sum + a.total_repos, 0)
    return (
      <div className="text-center py-4">
        <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--bg-secondary)]/30 px-5 py-2 text-sm text-[var(--text-secondary)] mb-8">
          <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          Research Data &bull; {monthRange}
        </div>

        <h1 className="text-4xl font-bold text-[var(--text-primary)] sm:text-5xl lg:text-6xl mb-4">
          <span className="gradient-text">AI Coding Agents</span>
          <br />
          <span className="text-[var(--text-primary)]">Industry Adoption Analysis</span>
        </h1>
        <p className="text-lg text-[var(--text-secondary)] max-w-2xl mx-auto mb-10">
          Comprehensive research tracking how different industries adopt AI-powered coding
          assistants across {formatNumber(totalRepos)}+ public GitHub repositories, classified by NAICS industry codes.
        </p>

        <div className="flex justify-center gap-8 sm:gap-12 flex-wrap">
          <StatCounter value={totalRepos >= 1000000 ? `${(totalRepos / 1000000).toFixed(1)}M+` : `${Math.round(totalRepos / 1000)}K+`} label="Repositories Analyzed" />
          <StatCounter value={String(INDUSTRIES.length)} label="Industries Tracked" />
          <StatCounter value={String(agents.length)} label="AI Agents Compared" />
        </div>

        <button
          onClick={downloadAllData}
          disabled={downloading}
          className="inline-flex items-center gap-2 mt-8 px-5 py-2.5 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)]/50 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50"
        >
          <Download className="h-4 w-4" />
          {downloading ? 'Downloading...' : 'Download All Data (CSV)'}
        </button>
      </div>
    )
  }

  // Single agent mode
  const agent = agents.find(a => a.id === selectedAgent)
  if (!agent) return null

  const stats = allAgentStats[selectedAgent]
  const agentStaticStats = AGENT_STATS[selectedAgent]
  const company = AGENT_COMPANIES[selectedAgent]
  const totalRepos = stats?.industryTotals.reduce((sum, i) => sum + i.value, 0) || agent.total_repos
  const topIndustry = stats?.industryTotals.length
    ? [...stats.industryTotals].sort((a, b) => b.value - a.value)[0]
    : null

  return (
    <div className="py-4">
      <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--bg-secondary)]/30 px-4 py-1.5 text-xs text-[var(--text-secondary)] mb-6">
        <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
        Live Data Visualization
      </div>

      <div className="flex items-center gap-3 mb-2">
        <div className="w-4 h-4 rounded-full" style={{ backgroundColor: agent.color }} />
        <h1 className="text-3xl sm:text-4xl font-bold text-[var(--text-primary)]">
          <span style={{ color: agent.color }}>{agent.name}</span>
        </h1>
      </div>
      <p className="text-[var(--text-secondary)] max-w-2xl mb-8">
        Industry adoption analysis across {formatNumber(totalRepos)}+ repositories
        {company && <span className="text-[var(--text-muted)]"> — by {company}</span>}
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <MiniStat
          label="Total Repos"
          value={agentStaticStats?.repos || formatNumber(totalRepos)}
          color={agent.color}
        />
        <MiniStat
          label="Prof. Services"
          value={agentStaticStats?.profServices || '—'}
          color={agent.color}
        />
        <MiniStat
          label="Months Data"
          value={String(agentStaticStats?.months || stats?.months.length || '—')}
          color={agent.color}
        />
        <MiniStat
          label="Top Industry"
          value={topIndustry?.name || '—'}
          color={topIndustry?.color || agent.color}
          small
        />
      </div>
    </div>
  )
}

function StatCounter({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <div className="text-4xl sm:text-5xl font-extrabold text-purple-400">{value}</div>
      <div className="text-sm text-[var(--text-muted)] mt-1">{label}</div>
    </div>
  )
}

function MiniStat({ label, value, color, small }: { label: string; value: string; color: string; small?: boolean }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)]/30 backdrop-blur-sm p-4">
      <p className="text-sm text-[var(--text-secondary)] mb-1">{label}</p>
      <p className={small ? 'text-lg font-semibold' : 'text-2xl font-bold'} style={{ color }}>
        {value}
      </p>
    </div>
  )
}
