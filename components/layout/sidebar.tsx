'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { useAgentSelection, AgentSelection } from '@/lib/agent-context'
import { AGENTS } from '@/lib/constants'
import { Filter, X } from 'lucide-react'

const agentOptions: { id: AgentSelection; name: string; color: string }[] = [
  { id: 'all', name: 'All Agents', color: '#a78bfa' },
  ...AGENTS.map(a => ({ id: a.id as AgentSelection, name: a.name, color: a.color })),
]

export function Sidebar() {
  const { selectedAgent, setSelectedAgent } = useAgentSelection()
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <>
      {/* Mobile FAB toggle */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed bottom-6 left-6 z-50 flex items-center gap-2 px-4 py-3 rounded-full bg-purple-600 text-white shadow-lg shadow-purple-900/30 hover:bg-purple-500 transition-colors"
      >
        <Filter className="h-4 w-4" />
        <span className="text-sm font-medium">Agents</span>
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={cn(
          'hidden lg:block lg:sticky lg:top-16 lg:h-[calc(100vh-4rem)] lg:w-56 lg:shrink-0',
          'lg:overflow-y-auto lg:border-r lg:border-[var(--border)]',
          'lg:bg-[var(--bg-primary)]/60 lg:backdrop-blur-md',
        )}
      >
        <SidebarContent
          selectedAgent={selectedAgent}
          onSelect={(agent) => setSelectedAgent(agent)}
        />
      </aside>

      {/* Mobile drawer */}
      <aside
        className={cn(
          'lg:hidden fixed inset-y-0 left-0 z-50 w-64 bg-[var(--bg-primary)] border-r border-[var(--border)]',
          'transform transition-transform duration-300 ease-out',
          mobileOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
          <span className="text-sm font-semibold text-[var(--text-secondary)]">Filter Agents</span>
          <button onClick={() => setMobileOpen(false)} className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
            <X className="h-5 w-5" />
          </button>
        </div>
        <SidebarContent
          selectedAgent={selectedAgent}
          onSelect={(agent) => {
            setSelectedAgent(agent)
            setMobileOpen(false)
          }}
        />
      </aside>
    </>
  )
}

function SidebarContent({
  selectedAgent,
  onSelect,
}: {
  selectedAgent: AgentSelection
  onSelect: (agent: AgentSelection) => void
}) {
  return (
    <div className="p-4 space-y-6">
      {/* Agent Selection */}
      <div>
        <h3 className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider mb-3">
          AI Agent
        </h3>
        <div className="space-y-1">
          {agentOptions.map((agent) => (
            <button
              key={agent.id}
              onClick={() => onSelect(agent.id)}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                selectedAgent === agent.id
                  ? 'bg-[var(--bg-tertiary)] text-[var(--text-primary)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]/50 hover:text-[var(--text-primary)]'
              )}
            >
              <div
                className="w-3 h-3 rounded-full shrink-0 ring-2 ring-offset-1 ring-offset-[var(--bg-primary)]"
                style={{
                  backgroundColor: selectedAgent === agent.id ? agent.color : 'transparent',
                  border: `2px solid ${agent.color}`,
                }}
              />
              <span className="truncate">{agent.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-[var(--border)]" />

      {/* Quick nav */}
      <div>
        <h3 className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider mb-3">
          Sections
        </h3>
        <div className="space-y-1">
          {[
            { id: 'hero', label: 'Overview' },
            { id: 'comparison', label: 'Comparison' },
            { id: 'industries', label: 'Industries' },
            { id: 'trends', label: 'Trends' },
            { id: 'findings', label: 'Findings' },
            { id: 'methodology', label: 'Methodology' },
          ].map((section) => (
            <button
              key={section.id}
              onClick={() => {
                document.getElementById(section.id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
              }}
              className="w-full text-left px-3 py-1.5 rounded-md text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]/30 transition-colors"
            >
              {section.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
