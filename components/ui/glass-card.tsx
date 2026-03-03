import { cn } from '@/lib/utils'
import { ReactNode } from 'react'

interface GlassCardProps {
  children: ReactNode
  className?: string
}

export function GlassCard({ children, className }: GlassCardProps) {
  return (
    <div
      className={cn(
        'rounded-2xl border border-[var(--border)]',
        'bg-[var(--glass-bg)] backdrop-blur-xl',
        'p-3 sm:p-6 lg:p-8',
        'shadow-[0_0_40px_var(--glass-shadow)]',
        className
      )}
    >
      {children}
    </div>
  )
}
