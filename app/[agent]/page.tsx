import { AGENTS } from '@/lib/constants'
import { ClientRedirect } from '@/components/client-redirect'

export function generateStaticParams() {
  return AGENTS.map((agent) => ({
    agent: agent.id,
  }))
}

const BASE_PATH = '/ai-coding-agents-industry-analysis'

interface PageProps {
  params: Promise<{ agent: string }>
}

export default async function AgentPage({ params }: PageProps) {
  const { agent } = await params
  const valid = AGENTS.some(a => a.id === agent)
  const url = valid
    ? `${BASE_PATH}/?agent=${agent}#comparison`
    : `${BASE_PATH}/`
  return <ClientRedirect url={url} />
}
