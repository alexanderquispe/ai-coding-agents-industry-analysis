'use client'

import { createContext, useContext, useState, ReactNode } from 'react'

export type AgentSelection = 'all' | 'claude' | 'copilot' | 'codex' | 'cursor'

interface AgentContextType {
  selectedAgent: AgentSelection
  setSelectedAgent: (agent: AgentSelection) => void
}

const AgentContext = createContext<AgentContextType | undefined>(undefined)

export function AgentProvider({ children }: { children: ReactNode }) {
  const [selectedAgent, setSelectedAgent] = useState<AgentSelection>('all')
  return (
    <AgentContext.Provider value={{ selectedAgent, setSelectedAgent }}>
      {children}
    </AgentContext.Provider>
  )
}

export function useAgentSelection() {
  const context = useContext(AgentContext)
  if (!context) throw new Error('useAgentSelection must be used within AgentProvider')
  return context
}
