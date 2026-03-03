export interface Agent {
  id: string
  name: string
  color: string
  total_repos: number
  created_at?: string
}

export interface Industry {
  code: string
  name: string
  description?: string
  color: string
}

export interface MonthlyStat {
  id?: number
  agent_id: string
  industry_code: string
  month: string
  cumulative: number
  new_repos: number
}

export interface AgentWithStats extends Agent {
  monthly_stats: MonthlyStat[]
}

export interface ChartDataPoint {
  month: string
  [key: string]: string | number
}

export interface IndustryData {
  code: string
  name: string
  color: string
  values: number[]
  monthly: number[]
}

export interface CumulativeJson {
  agent: string
  total_repos: number
  months: string[]
  industries: IndustryData[]
}
