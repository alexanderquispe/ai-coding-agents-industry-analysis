'use client'

import { useTheme } from './theme-context'

const chartColors = {
  dark: {
    grid: '#27272a',
    axis: '#71717a',
    tick: '#a1a1aa',
    tooltipBg: '#18181b',
    tooltipBorder: '#27272a',
    tooltipLabel: '#fafafa',
    legendText: '#a1a1aa',
  },
  light: {
    grid: '#e4e4e7',
    axis: '#a1a1aa',
    tick: '#71717a',
    tooltipBg: '#ffffff',
    tooltipBorder: '#e4e4e7',
    tooltipLabel: '#18181b',
    legendText: '#71717a',
  },
} as const

export function useChartColors() {
  const { resolvedTheme } = useTheme()
  return chartColors[resolvedTheme]
}
