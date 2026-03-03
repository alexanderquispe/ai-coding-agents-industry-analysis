'use client'

import { useState, useMemo } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { formatNumber, formatMonth } from '@/lib/utils'
import { Industry } from '@/lib/types'
import { useChartColors } from '@/lib/use-chart-colors'

interface CumulativeChartProps {
  data: Record<string, string | number>[]
  industries: Industry[]
}

export function CumulativeChart({ data, industries }: CumulativeChartProps) {
  const colors = useChartColors()
  const [topN, setTopN] = useState<'top5' | 'top10' | 'all'>('top10')
  const [scale, setScale] = useState<'linear' | 'log'>('linear')
  const [hiddenCodes, setHiddenCodes] = useState<Set<string>>(new Set())

  // Sort industries by total value
  const sortedIndustries = useMemo(() => {
    return [...industries].sort((a, b) => {
      const lastData = data[data.length - 1]
      if (!lastData) return 0
      const aVal = (lastData[a.code] as number) || 0
      const bVal = (lastData[b.code] as number) || 0
      return bVal - aVal
    })
  }, [industries, data])

  // Filter by topN
  const visibleIndustries = useMemo(() => {
    let filtered = sortedIndustries
    if (topN === 'top5') filtered = sortedIndustries.slice(0, 5)
    else if (topN === 'top10') filtered = sortedIndustries.slice(0, 10)
    return filtered.filter((i) => !hiddenCodes.has(i.code))
  }, [sortedIndustries, topN, hiddenCodes])

  // Industries available for legend (based on topN filter)
  const legendIndustries = useMemo(() => {
    if (topN === 'top5') return sortedIndustries.slice(0, 5)
    if (topN === 'top10') return sortedIndustries.slice(0, 10)
    return sortedIndustries
  }, [sortedIndustries, topN])

  const toggleIndustry = (code: string) => {
    setHiddenCodes((prev) => {
      const next = new Set(prev)
      if (next.has(code)) next.delete(code)
      else next.add(code)
      return next
    })
  }

  // Stack order: smallest on top
  const stackedIndustries = [...visibleIndustries].reverse()

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--text-muted)]">Industries:</span>
          <select
            className="bg-[var(--bg-tertiary)] border border-[var(--border)] text-[var(--text-primary)] text-xs rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-purple-500"
            value={topN}
            onChange={(e) => setTopN(e.target.value as 'top5' | 'top10' | 'all')}
          >
            <option value="top5">Top 5</option>
            <option value="top10">Top 10</option>
            <option value="all">All {industries.length}</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--text-muted)]">Scale:</span>
          <select
            className="bg-[var(--bg-tertiary)] border border-[var(--border)] text-[var(--text-primary)] text-xs rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-purple-500"
            value={scale}
            onChange={(e) => setScale(e.target.value as 'linear' | 'log')}
          >
            <option value="linear">Linear</option>
            <option value="log">Logarithmic</option>
          </select>
        </div>
      </div>

      {/* Chart */}
      <div className="h-[400px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 5, left: -10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
            <XAxis
              dataKey="month"
              stroke={colors.axis}
              fontSize={12}
              tickFormatter={formatMonth}
              tick={{ fill: colors.tick }}
            />
            <YAxis
              stroke={colors.axis}
              fontSize={12}
              tickFormatter={formatNumber}
              tick={{ fill: colors.tick }}
              scale={scale === 'log' ? 'log' : 'auto'}
              domain={scale === 'log' ? [1, 'auto'] : [0, 'auto']}
              allowDataOverflow={scale === 'log'}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: colors.tooltipBg,
                border: `1px solid ${colors.tooltipBorder}`,
                borderRadius: '8px',
                maxHeight: '300px',
                overflowY: 'auto',
              }}
              labelStyle={{ color: colors.tooltipLabel }}
              labelFormatter={(label) => formatMonth(String(label))}
              formatter={(value, name) => {
                const industry = industries.find((i) => i.code === name)
                return [formatNumber(Number(value) || 0), industry?.name || String(name)]
              }}
            />
            {stackedIndustries.map((industry) => (
              <Area
                key={industry.code}
                type="monotone"
                dataKey={industry.code}
                name={industry.code}
                stackId="1"
                stroke={industry.color}
                fill={industry.color}
                fillOpacity={0.6}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Clickable Legend */}
      <div className="flex flex-wrap gap-3 justify-center">
        {legendIndustries.map((industry) => {
          const isHidden = hiddenCodes.has(industry.code)
          return (
            <button
              key={industry.code}
              className={`flex items-center gap-1.5 transition-opacity cursor-pointer hover:opacity-80 ${
                isHidden ? 'opacity-30' : 'opacity-100'
              }`}
              onClick={() => toggleIndustry(industry.code)}
              type="button"
            >
              <div
                className="w-3 h-3 rounded-sm"
                style={{ backgroundColor: industry.color }}
              />
              <span className="text-xs text-[var(--text-secondary)]">{industry.name}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
