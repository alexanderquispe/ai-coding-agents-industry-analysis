import { getSupabase, isSupabaseConfigured } from './supabase'
import { Agent, Industry, MonthlyStat, AgentWithStats } from './types'
import { AGENTS, INDUSTRIES } from './constants'
import fs from 'fs'
import path from 'path'

// Fallback to JSON files when Supabase is not configured
function loadJsonData(agentId: string) {
  try {
    const jsonPath = path.join(
      process.cwd(),
      'public',
      'data',
      `${agentId}_cumulative.json`
    )
    if (fs.existsSync(jsonPath)) {
      return JSON.parse(fs.readFileSync(jsonPath, 'utf-8'))
    }
  } catch {
    // File not found or invalid
  }
  return null
}

export async function getAgents(): Promise<Agent[]> {
  if (!isSupabaseConfigured()) {
    return AGENTS.map(agent => {
      const data = loadJsonData(agent.id)
      return {
        ...agent,
        total_repos: data?.total_repos || 0
      }
    })
  }

  const supabase = getSupabase()
  if (!supabase) return AGENTS

  const { data, error } = await supabase
    .from('agents')
    .select('*')
    .order('id')

  if (error) {
    console.error('Error fetching agents:', error)
    return AGENTS
  }
  return data || AGENTS
}

export async function getAgent(agentId: string): Promise<Agent | null> {
  if (!isSupabaseConfigured()) {
    const agent = AGENTS.find(a => a.id === agentId)
    if (agent) {
      const data = loadJsonData(agentId)
      return { ...agent, total_repos: data?.total_repos || 0 }
    }
    return null
  }

  const supabase = getSupabase()
  if (!supabase) {
    const agent = AGENTS.find(a => a.id === agentId)
    return agent || null
  }

  const { data, error } = await supabase
    .from('agents')
    .select('*')
    .eq('id', agentId)
    .single()

  if (error) {
    console.error('Error fetching agent:', error)
    return null
  }
  return data
}

export async function getIndustries(): Promise<Industry[]> {
  if (!isSupabaseConfigured()) {
    return INDUSTRIES
  }

  const supabase = getSupabase()
  if (!supabase) return INDUSTRIES

  const { data, error } = await supabase
    .from('industries')
    .select('*')
    .order('code')

  if (error) {
    console.error('Error fetching industries:', error)
    return INDUSTRIES
  }
  return data || INDUSTRIES
}

export async function getAgentStats(agentId: string): Promise<MonthlyStat[]> {
  if (!isSupabaseConfigured()) {
    const jsonData = loadJsonData(agentId)
    if (!jsonData) return []

    const stats: MonthlyStat[] = []
    for (const industry of jsonData.industries) {
      for (let i = 0; i < jsonData.months.length; i++) {
        stats.push({
          agent_id: agentId,
          industry_code: industry.code,
          month: jsonData.months[i],
          cumulative: industry.values[i],
          new_repos: industry.monthly[i]
        })
      }
    }
    return stats
  }

  const supabase = getSupabase()
  if (!supabase) return []

  const { data, error } = await supabase
    .from('monthly_stats')
    .select('*')
    .eq('agent_id', agentId)
    .order('month', { ascending: true })

  if (error) {
    console.error('Error fetching agent stats:', error)
    return []
  }
  return data || []
}

export async function getAllAgentsWithStats(): Promise<AgentWithStats[]> {
  const agents = await getAgents()
  const agentsWithStats: AgentWithStats[] = []

  for (const agent of agents) {
    const stats = await getAgentStats(agent.id)
    agentsWithStats.push({
      ...agent,
      monthly_stats: stats
    })
  }

  return agentsWithStats
}

export async function getLatestMonth(): Promise<string | null> {
  if (!isSupabaseConfigured()) {
    const jsonData = loadJsonData('claude')
    if (jsonData?.months?.length) {
      return jsonData.months[jsonData.months.length - 1]
    }
    return null
  }

  const supabase = getSupabase()
  if (!supabase) return null

  const { data, error } = await supabase
    .from('monthly_stats')
    .select('month')
    .order('month', { ascending: false })
    .limit(1)

  if (error || !data?.length) return null
  return data[0].month
}

export async function getAgentTotalByMonth(agentId: string): Promise<{ month: string; total: number }[]> {
  const stats = await getAgentStats(agentId)

  const monthTotals = new Map<string, number>()

  for (const stat of stats) {
    if (stat.month < '2025-01') continue
    const current = monthTotals.get(stat.month) || 0
    monthTotals.set(stat.month, current + stat.cumulative)
  }

  return Array.from(monthTotals.entries())
    .map(([month, total]) => ({ month, total }))
    .sort((a, b) => a.month.localeCompare(b.month))
}
