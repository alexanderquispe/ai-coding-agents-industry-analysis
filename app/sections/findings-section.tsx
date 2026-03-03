import { KEY_FINDINGS } from '@/lib/constants'
import { GlassCard } from '@/components/ui/glass-card'

export function FindingsSection() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">Key Findings</h2>
        <p className="text-[var(--text-secondary)]">Insights from analyzing industry adoption patterns</p>
      </div>

      <div className="space-y-4">
        {KEY_FINDINGS.map((finding) => (
          <GlassCard key={finding.number} className="flex gap-4 !p-5">
            <div className="text-2xl font-extrabold text-purple-400 min-w-[40px]">
              {finding.number}
            </div>
            <div>
              <h4 className="text-base font-semibold text-[var(--text-primary)] mb-1">
                {finding.title}
              </h4>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                {finding.description}
              </p>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  )
}
