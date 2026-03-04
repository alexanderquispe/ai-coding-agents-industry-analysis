'use client'

import { useEffect, useState } from 'react'

const EDGE_FUNCTION_URL = 'https://xplcfeqzkdxhklbimbte.supabase.co/functions/v1/track-visit'

export function VisitCounter() {
  const [count, setCount] = useState<number | null>(null)

  useEffect(() => {
    const tracked = sessionStorage.getItem('visit_tracked')
    if (tracked) {
      setCount(parseInt(tracked, 10))
      return
    }

    fetch(EDGE_FUNCTION_URL, { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        if (data.count) {
          setCount(data.count)
          sessionStorage.setItem('visit_tracked', String(data.count))
        }
      })
      .catch(() => {
        // Silent fail - counter is non-essential
      })
  }, [])

  if (count === null) return null

  return (
    <span className="text-xs text-[var(--text-muted)]">
      {count.toLocaleString()} visits
    </span>
  )
}
