'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { formatNumber, formatMonth } from '@/lib/utils'
import { useChartColors } from '@/lib/use-chart-colors'

interface AgentConfig {
  id: string
  name: string
  color: string
}

interface ComparisonChartProps {
  data: Record<string, string | number>[]
  agents: AgentConfig[]
}

export function ComparisonChart({ data, agents }: ComparisonChartProps) {
  const colors = useChartColors()

  return (
    <div className="h-[400px] w-full">
      <ResponsiveContainer width="100%" height="100%">
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
            contentStyle={{
              backgroundColor: colors.tooltipBg,
              border: `1px solid ${colors.tooltipBorder}`,
              borderRadius: '8px',
            }}
            labelStyle={{ color: colors.tooltipLabel }}
            labelFormatter={(label) => formatMonth(String(label))}
            formatter={(value, name) => {
              const agent = agents.find(a => a.id === name)
              return [formatNumber(Number(value) || 0), agent?.name || String(name)]
            }}
          />
          <Legend
            verticalAlign="bottom"
            wrapperStyle={{ paddingTop: '16px' }}
            formatter={(value: string) => {
              const agent = agents.find(a => a.id === value)
              return <span style={{ color: colors.legendText, fontSize: '11px' }}>{agent?.name || value}</span>
            }}
          />
          {agents.map((agent) => (
            <Line
              key={agent.id}
              type="monotone"
              dataKey={agent.id}
              name={agent.name}
              stroke={agent.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6, strokeWidth: 2 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
