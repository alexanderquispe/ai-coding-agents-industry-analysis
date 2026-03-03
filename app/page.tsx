import { getAgents, getAgentStats, getIndustries, getAgentTotalByMonth } from '@/lib/queries'
import { processStats, ProcessedAgentData } from '@/lib/data-processing'
import { DashboardContent } from './dashboard-content'
import { formatNumber } from '@/lib/utils'


function formatMonthShort(month: string): string {
  const [year, m] = month.split('-')
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${months[parseInt(m) - 1]} ${year}`
}

export default async function HomePage() {
  const [agents, industries] = await Promise.all([
    getAgents(),
    getIndustries(),
  ])

  // Load stats for ALL agents (for sidebar filtering)
  const allAgentStats: Record<string, ProcessedAgentData> = {}
  const agentStatsList = await Promise.all(
    agents.map(async (agent) => ({
      id: agent.id,
      stats: await getAgentStats(agent.id),
    }))
  )
  for (const { id, stats } of agentStatsList) {
    allAgentStats[id] = processStats(stats, industries)
  }

  // Build comparison data (multi-agent cumulative totals by month)
  const agentTotals = await Promise.all(
    agents.map(async (agent) => ({
      agent,
      totals: await getAgentTotalByMonth(agent.id),
    }))
  )

  const allMonths = new Set<string>()
  agentTotals.forEach(({ totals }) => {
    totals.forEach(({ month }) => allMonths.add(month))
  })

  const sortedMonths = Array.from(allMonths).sort()
  const comparisonData = sortedMonths.map((month) => {
    const point: Record<string, string | number> = { month }
    agentTotals.forEach(({ agent, totals }) => {
      const monthData = totals.find((t) => t.month === month)
      point[agent.id] = monthData?.total || 0
    })
    return point
  })

  // Hydrate agents with latest total
  const hydratedAgents = agents.map((agent) => {
    const agentData = agentTotals.find((at) => at.agent.id === agent.id)
    const latestTotal = agentData?.totals[agentData.totals.length - 1]?.total || 0
    return { ...agent, total_repos: latestTotal }
  })

  const monthRange = sortedMonths.length > 0
    ? `${formatMonthShort(sortedMonths[0])} - ${formatMonthShort(sortedMonths[sortedMonths.length - 1])}`
    : 'Jan 2025 - Feb 2026'

  return (
    <DashboardContent
      agents={hydratedAgents}
      industries={industries}
      allAgentStats={allAgentStats}
      comparisonData={comparisonData}
      monthRange={monthRange}
    />
  )
}
