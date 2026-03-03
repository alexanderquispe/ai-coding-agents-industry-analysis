'use client'

import { useInView } from 'react-intersection-observer'
import { cn } from '@/lib/utils'
import { ReactNode } from 'react'

interface FadeInSectionProps {
  children: ReactNode
  className?: string
  id?: string
  threshold?: number
  delay?: number
}

export function FadeInSection({ children, className, id, threshold = 0.1, delay = 0 }: FadeInSectionProps) {
  const { ref, inView } = useInView({
    triggerOnce: true,
    threshold,
  })

  return (
    <section
      ref={ref}
      id={id}
      className={cn(
        'transition-all duration-700 ease-out',
        inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8',
        className
      )}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </section>
  )
}
