import { MonthlyStat, Industry } from './types'

export interface ProcessedAgentData {
  months: string[]
  cumulativeData: Record<string, string | number>[]
  monthlyData: Record<string, string | number>[]
  industryTotals: { code: string; name: string; value: number; color: string }[]
  timeData: { code: string; name: string; color: string; values: number[] }[]
}

const MIN_MONTH = '2025-01'

export function processStats(stats: MonthlyStat[], industries: Industry[]): ProcessedAgentData {
  const filtered = stats.filter((s) => s.month >= MIN_MONTH)
  const months = [...new Set(filtered.map((s) => s.month))].sort()

  // Build cumulative data (stacked area chart)
  const cumulativeData = months.map((month) => {
    const point: Record<string, string | number> = { month }
    industries.forEach((ind) => {
      const stat = filtered.find(
        (s) => s.month === month && s.industry_code === ind.code
      )
      point[ind.code] = stat?.cumulative || 0
    })
    return point
  })

  // Build monthly data (bar chart)
  const monthlyData = months.map((month) => {
    const point: Record<string, string | number> = { month }
    industries.forEach((ind) => {
      const stat = filtered.find(
        (s) => s.month === month && s.industry_code === ind.code
      )
      point[ind.code] = stat?.new_repos || 0
    })
    return point
  })

  // Build industry totals for bar race (latest month)
  const industryTotals = industries.map((ind) => {
    const latestMonth = months[months.length - 1]
    const stat = stats.find(
      (s) => s.month === latestMonth && s.industry_code === ind.code
    )
    return {
      code: ind.code,
      name: ind.name,
      value: stat?.cumulative || 0,
      color: ind.color,
    }
  })

  // Build time series data for bar race animation
  const timeData = industries.map((ind) => ({
    code: ind.code,
    name: ind.name,
    color: ind.color,
    values: months.map((month) => {
      const stat = filtered.find(
        (s) => s.month === month && s.industry_code === ind.code
      )
      return stat?.cumulative || 0
    }),
  }))

  return { months, cumulativeData, monthlyData, industryTotals, timeData }
}
