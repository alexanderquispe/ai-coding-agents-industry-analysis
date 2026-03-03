'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { formatNumber } from '@/lib/utils'
import { Industry } from '@/lib/types'
import { Play, Pause, RotateCcw } from 'lucide-react'

interface IndustryValue {
  code: string
  name: string
  value: number
  color: string
}

// Data for all months, used by the animated bar race
interface BarRaceTimeData {
  code: string
  name: string
  color: string
  values: number[] // One value per month
}

interface IndustryBarRaceProps {
  data: IndustryValue[]
  maxItems?: number
  // Optional: time series data for animation
  timeData?: BarRaceTimeData[]
  months?: string[]
}

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function formatMonthLabel(month: string): string {
  const [year, m] = month.split('-')
  return `${MONTH_NAMES[parseInt(m) - 1]} ${year}`
}

export function IndustryBarRace({ data, maxItems = 10, timeData, months }: IndustryBarRaceProps) {
  const hasTimeSeries = timeData && months && months.length > 0
  const [currentIndex, setCurrentIndex] = useState(hasTimeSeries ? months!.length - 1 : 0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState(800)
  const [showAll, setShowAll] = useState(true)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Compute current values based on month index
  const currentData: IndustryValue[] = hasTimeSeries
    ? timeData!.map((ind) => ({
        code: ind.code,
        name: ind.name,
        value: ind.values[currentIndex] || 0,
        color: ind.color,
      }))
    : data

  const sortedData = [...currentData]
    .sort((a, b) => b.value - a.value)

  const displayData = showAll ? sortedData : sortedData.slice(0, maxItems)
  const maxValue = sortedData[0]?.value || 1

  // Animation controls
  const play = useCallback(() => {
    if (!hasTimeSeries) return
    setIsPlaying(true)
  }, [hasTimeSeries])

  const pause = useCallback(() => {
    setIsPlaying(false)
  }, [])

  const reset = useCallback(() => {
    setIsPlaying(false)
    setCurrentIndex(0)
  }, [])

  useEffect(() => {
    if (isPlaying && hasTimeSeries) {
      intervalRef.current = setInterval(() => {
        setCurrentIndex((prev) => {
          if (prev >= months!.length - 1) {
            setIsPlaying(false)
            return prev
          }
          return prev + 1
        })
      }, speed)
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [isPlaying, speed, hasTimeSeries, months])

  const progressPct = hasTimeSeries ? ((currentIndex + 1) / months!.length) * 100 : 100

  return (
    <div className="space-y-4">
      {/* Controls Header */}
      {hasTimeSeries && (
        <div className="flex flex-wrap items-center gap-3">
          {/* Month Selector */}
          <select
            className="bg-[var(--bg-tertiary)] border border-[var(--border)] text-[var(--text-primary)] text-sm rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-purple-500"
            value={currentIndex}
            onChange={(e) => {
              setIsPlaying(false)
              setCurrentIndex(Number(e.target.value))
            }}
          >
            {months!.map((m, i) => (
              <option key={m} value={i}>{formatMonthLabel(m)}</option>
            ))}
          </select>

          <span className="text-xs text-[var(--text-muted)]">Cumulative adoption by NAICS sector</span>

          <div className="flex-1" />

          {/* Play/Pause */}
          <button
            onClick={isPlaying ? pause : play}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium transition-colors"
          >
            {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
            {isPlaying ? 'Pause' : 'Play'}
          </button>

          {/* Reset */}
          <button
            onClick={reset}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[var(--bg-tertiary)] hover:brightness-110 text-[var(--text-primary)] text-xs font-medium transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset
          </button>

          {/* Speed */}
          <select
            className="bg-[var(--bg-tertiary)] border border-[var(--border)] text-[var(--text-primary)] text-xs rounded-md px-2 py-1.5 focus:outline-none"
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value))}
          >
            <option value={1200}>0.5x</option>
            <option value={800}>1x</option>
            <option value={400}>2x</option>
            <option value={200}>4x</option>
          </select>

          {/* Toggle */}
          <button
            onClick={() => setShowAll(!showAll)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              showAll
                ? 'bg-purple-600/20 text-purple-400 border border-purple-500/30'
                : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border border-[var(--border)]'
            }`}
          >
            {showAll ? `All ${sortedData.length}` : `Top ${maxItems}`}
          </button>
        </div>
      )}

      {/* Bar items */}
      <div className="space-y-1">
        {displayData.map((item, index) => {
          const pct = (item.value / maxValue) * 100
          return (
            <div
              key={item.code}
              className="relative h-7 bg-[var(--bar-bg)] rounded overflow-hidden transition-all duration-300"
            >
              {/* Bar fill */}
              <div
                className="absolute inset-y-0 left-0 rounded transition-all duration-500"
                style={{
                  width: `${pct}%`,
                  background: `linear-gradient(90deg, ${item.color}80, ${item.color})`,
                }}
              />
              {/* Text overlay inside bar */}
              <div className="relative h-full flex items-center justify-between px-2 z-10">
                <div className="flex items-center gap-1.5 min-w-0">
                  <span className="text-[10px] font-bold text-white/60 shrink-0">
                    {index + 1}
                  </span>
                  <span className="text-[11px] font-medium text-white truncate drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]">
                    {item.name}
                  </span>
                </div>
                <span className="text-[11px] font-mono text-white shrink-0 ml-1 drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]">
                  {formatNumber(item.value)}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Progress bar */}
      {hasTimeSeries && (
        <div className="pt-3 border-t border-[var(--border)]">
          <div className="flex justify-between mb-2">
            <span className="text-xs text-[var(--text-muted)]">Timeline Progress</span>
            <span className="text-xs text-[var(--text-muted)]">
              {currentIndex + 1} of {months!.length} months
            </span>
          </div>
          <div className="h-1 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-600 to-pink-500 rounded-full transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

interface IndustryLegendProps {
  industries: Industry[]
  hiddenCodes?: Set<string>
  onToggle?: (code: string) => void
}

export function IndustryLegend({ industries, hiddenCodes, onToggle }: IndustryLegendProps) {
  return (
    <div className="flex flex-wrap gap-3 justify-center mt-4">
      {industries.map((industry) => {
        const isHidden = hiddenCodes?.has(industry.code)
        return (
          <button
            key={industry.code}
            className={`flex items-center gap-1.5 transition-opacity ${
              isHidden ? 'opacity-30' : 'opacity-100'
            } ${onToggle ? 'cursor-pointer hover:opacity-80' : 'cursor-default'}`}
            onClick={() => onToggle?.(industry.code)}
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
  )
}
