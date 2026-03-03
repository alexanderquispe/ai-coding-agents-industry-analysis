import { useRef, useCallback } from 'react'

/**
 * On real mobile devices, lifting your finger (touchend) does not fire
 * mouseleave, so Recharts tooltips stay visible forever.
 * This hook dispatches a synthetic mouseleave on the chart SVG
 * when the user lifts their finger, causing Recharts to hide the tooltip.
 */
export function useMobileTooltipDismiss() {
  const ref = useRef<HTMLDivElement>(null)

  const onTouchEnd = useCallback(() => {
    const svg = ref.current?.querySelector('svg')
    if (svg) {
      svg.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true }))
    }
  }, [])

  return { ref, onTouchEnd }
}
