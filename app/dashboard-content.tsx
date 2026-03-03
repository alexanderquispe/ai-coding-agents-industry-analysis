'use client'

import { useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useAgentSelection, AgentSelection } from '@/lib/agent-context'
import { FadeInSection } from '@/components/ui/fade-in-section'
import { GlassCard } from '@/components/ui/glass-card'
import { ComparisonChart } from '@/components/charts/comparison-chart'
import { CumulativeChart } from '@/components/charts/cumulative-chart'
import { MonthlyChart } from '@/components/charts/monthly-chart'
import { IndustryBarRace } from '@/components/charts/industry-bar-race'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { HeroSection } from './sections/hero-section'
import { FindingsSection } from './sections/findings-section'
import { MethodologySection } from './sections/methodology-section'
import { Footer } from '@/components/layout/footer'
import { Agent, Industry } from '@/lib/types'
import { ProcessedAgentData } from '@/lib/data-processing'

interface DashboardContentProps {
  agents: Agent[]
  industries: Industry[]
  allAgentStats: Record<string, ProcessedAgentData>
  comparisonData: Record<string, string | number>[]
  monthRange: string
}

function DashboardInner({ agents, industries, allAgentStats, comparisonData, monthRange }: DashboardContentProps) {
  const { selectedAgent, setSelectedAgent } = useAgentSelection()
  const searchParams = useSearchParams()

  // Deep-link support: ?agent=claude
  useEffect(() => {
    const agentParam = searchParams.get('agent')
    if (agentParam && ['claude', 'copilot', 'codex', 'cursor'].includes(agentParam)) {
      setSelectedAgent(agentParam as AgentSelection)
    }
  }, [searchParams, setSelectedAgent])

  const isAllAgents = selectedAgent === 'all'
  const currentStats = !isAllAgents ? allAgentStats[selectedAgent] : null
  const currentAgent = !isAllAgents ? agents.find(a => a.id === selectedAgent) : null

  return (
    <div className="max-w-6xl mx-auto px-2 sm:px-6 lg:px-8 py-8 space-y-16">
      {/* HERO */}
      <FadeInSection id="hero">
        <HeroSection
          agents={agents}
          allAgentStats={allAgentStats}
          monthRange={monthRange}
        />
      </FadeInSection>

      {/* COMPARISON / CUMULATIVE */}
      <FadeInSection id="comparison">
        <GlassCard>
          {isAllAgents ? (
            <>
              <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Cumulative Adoption Comparison</h2>
              <ComparisonChart
                data={comparisonData}
                agents={agents.map(a => ({ id: a.id, name: a.name, color: a.color }))}
              />
            </>
          ) : currentStats ? (
            <>
              <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">
                <span style={{ color: currentAgent?.color }}>{currentAgent?.name}</span> — Cumulative by Industry
              </h2>
              <CumulativeChart data={currentStats.cumulativeData} industries={industries} />
            </>
          ) : null}
        </GlassCard>
      </FadeInSection>

      {/* INDUSTRIES - BAR RACE */}
      <FadeInSection id="industries">
        <GlassCard>
          <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Industry Distribution</h2>
          {isAllAgents ? (
            <Tabs defaultValue={agents[0]?.id}>
              <TabsList>
                {agents.map(agent => (
                  <TabsTrigger key={agent.id} value={agent.id}>
                    {agent.name}
                  </TabsTrigger>
                ))}
              </TabsList>
              {agents.map(agent => {
                const stats = allAgentStats[agent.id]
                return (
                  <TabsContent key={agent.id} value={agent.id}>
                    {stats && (
                      <IndustryBarRace
                        data={stats.industryTotals}
                        maxItems={10}
                        timeData={stats.timeData}
                        months={stats.months}
                      />
                    )}
                  </TabsContent>
                )
              })}
            </Tabs>
          ) : currentStats ? (
            <IndustryBarRace
              data={currentStats.industryTotals}
              maxItems={10}
              timeData={currentStats.timeData}
              months={currentStats.months}
            />
          ) : null}
        </GlassCard>
      </FadeInSection>

      {/* TRENDS - MONTHLY */}
      <FadeInSection id="trends">
        <GlassCard>
          <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Monthly Trends</h2>
          {isAllAgents ? (
            <Tabs defaultValue={agents[0]?.id}>
              <TabsList>
                {agents.map(agent => (
                  <TabsTrigger key={agent.id} value={agent.id}>
                    {agent.name}
                  </TabsTrigger>
                ))}
              </TabsList>
              {agents.map(agent => {
                const stats = allAgentStats[agent.id]
                return (
                  <TabsContent key={agent.id} value={agent.id}>
                    {stats && (
                      <MonthlyChart data={stats.monthlyData} industries={industries} />
                    )}
                  </TabsContent>
                )
              })}
            </Tabs>
          ) : currentStats ? (
            <MonthlyChart data={currentStats.monthlyData} industries={industries} />
          ) : null}
        </GlassCard>
      </FadeInSection>

      {/* FINDINGS */}
      <FadeInSection id="findings">
        <FindingsSection />
      </FadeInSection>

      {/* METHODOLOGY */}
      <FadeInSection id="methodology">
        <MethodologySection />
      </FadeInSection>

      {/* FOOTER */}
      <Footer />
    </div>
  )
}

export function DashboardContent(props: DashboardContentProps) {
  return (
    <Suspense>
      <DashboardInner {...props} />
    </Suspense>
  )
}
