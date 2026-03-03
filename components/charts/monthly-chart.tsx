'use client'

import { useState, useMemo } from 'react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { formatNumber, formatMonth } from '@/lib/utils'
import { Industry } from '@/lib/types'
import { useChartColors } from '@/lib/use-chart-colors'

interface MonthlyChartProps {
  data: Record<string, string | number>[]
  industries: Industry[]
}

export function MonthlyChart({ data, industries }: MonthlyChartProps) {
  const colors = useChartColors()
  const [topN, setTopN] = useState<'top5' | 'top10' | 'all'>('top10')
  const [chartType, setChartType] = useState<'line' | 'bar'>('line')
  const [hiddenCodes, setHiddenCodes] = useState<Set<string>>(new Set())

  // Sort industries by total value
  const sortedIndustries = useMemo(() => {
    return [...industries].sort((a, b) => {
      const totalA = data.reduce((sum, d) => sum + ((d[a.code] as number) || 0), 0)
      const totalB = data.reduce((sum, d) => sum + ((d[b.code] as number) || 0), 0)
      return totalB - totalA
    })
  }, [industries, data])

  // Filter by topN
  const visibleIndustries = useMemo(() => {
    let filtered = sortedIndustries
    if (topN === 'top5') filtered = sortedIndustries.slice(0, 5)
    else if (topN === 'top10') filtered = sortedIndustries.slice(0, 10)
    return filtered.filter((i) => !hiddenCodes.has(i.code))
  }, [sortedIndustries, topN, hiddenCodes])

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

  const tooltipContentStyle = {
    backgroundColor: colors.tooltipBg,
    border: `1px solid ${colors.tooltipBorder}`,
    borderRadius: '8px',
    maxHeight: '300px',
    overflowY: 'auto' as const,
  }

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
          <span className="text-xs text-[var(--text-muted)]">Chart Type:</span>
          <select
            className="bg-[var(--bg-tertiary)] border border-[var(--border)] text-[var(--text-primary)] text-xs rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-purple-500"
            value={chartType}
            onChange={(e) => setChartType(e.target.value as 'line' | 'bar')}
          >
            <option value="line">Line</option>
            <option value="bar">Stacked Bar</option>
          </select>
        </div>
      </div>

      {/* Chart */}
      <div className="h-[400px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'bar' ? (
            <BarChart
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
              />
              <Tooltip
                contentStyle={tooltipContentStyle}
                labelStyle={{ color: colors.tooltipLabel }}
                labelFormatter={(label) => formatMonth(String(label))}
                formatter={(value, name) => {
                  const industry = industries.find((i) => i.code === name)
                  return [formatNumber(Number(value) || 0), industry?.name || String(name)]
                }}
              />
              {visibleIndustries.map((industry) => (
                <Bar
                  key={industry.code}
                  dataKey={industry.code}
                  name={industry.code}
                  stackId="a"
                  fill={industry.color}
                />
              ))}
            </BarChart>
          ) : (
            <LineChart
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
              />
              <Tooltip
                contentStyle={tooltipContentStyle}
                labelStyle={{ color: colors.tooltipLabel }}
                labelFormatter={(label) => formatMonth(String(label))}
                formatter={(value, name) => {
                  const industry = industries.find((i) => i.code === name)
                  return [formatNumber(Number(value) || 0), industry?.name || String(name)]
                }}
              />
              {visibleIndustries.map((industry) => (
                <Line
                  key={industry.code}
                  type="monotone"
                  dataKey={industry.code}
                  name={industry.code}
                  stroke={industry.color}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              ))}
            </LineChart>
          )}
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
