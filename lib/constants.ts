import { Agent, Industry } from './types'

export const AGENTS: Agent[] = [
  { id: 'claude', name: 'Claude Code', color: '#a371f7', total_repos: 0 },
  { id: 'copilot', name: 'GitHub Copilot', color: '#58a6ff', total_repos: 0 },
  { id: 'codex', name: 'OpenAI Codex', color: '#3fb950', total_repos: 0 },
  { id: 'cursor', name: 'Cursor AI', color: '#f78166', total_repos: 0 },
]

export const INDUSTRIES: Industry[] = [
  { code: '54', name: 'Professional Services', color: '#7c3aed' },
  { code: '51', name: 'Information', color: '#2563eb' },
  { code: '52', name: 'Finance & Insurance', color: '#ca8a04' },
  { code: '61', name: 'Education', color: '#dc2626' },
  { code: '71', name: 'Entertainment', color: '#db2777' },
  { code: '56', name: 'Admin Services', color: '#16a34a' },
  { code: '81', name: 'Other Services', color: '#0891b2' },
  { code: '48-49', name: 'Transportation', color: '#7c3aed' },
  { code: '44-45', name: 'Retail Trade', color: '#0d9488' },
  { code: '62', name: 'Healthcare', color: '#ea580c' },
  { code: '31-33', name: 'Manufacturing', color: '#475569' },
  { code: '92', name: 'Public Admin', color: '#0284c7' },
  { code: '11', name: 'Agriculture', color: '#65a30d' },
  { code: '72', name: 'Accommodation', color: '#e11d48' },
  { code: '53', name: 'Real Estate', color: '#059669' },
  { code: '22', name: 'Utilities', color: '#4f46e5' },
  { code: '23', name: 'Construction', color: '#d97706' },
  { code: '42', name: 'Wholesale Trade', color: '#57534e' },
  { code: '21', name: 'Mining', color: '#78350f' },
]

export const AGENT_DESCRIPTIONS: Record<string, string> = {
  claude: 'Anthropic\'s AI coding assistant that helps with code generation, debugging, and software development tasks.',
  copilot: 'GitHub\'s AI pair programmer that suggests code completions and entire functions in real-time.',
  codex: 'OpenAI\'s AI system that translates natural language to code, powering various coding tools.',
  cursor: 'AI-first code editor that integrates AI assistance directly into the development workflow.',
}

export const NAICS_DESCRIPTIONS: Record<string, string> = {
  '54': 'Professional, Scientific, and Technical Services - Includes legal, accounting, engineering, research, and consulting services.',
  '51': 'Information - Publishing, broadcasting, telecommunications, data processing, and software.',
  '52': 'Finance and Insurance - Banks, credit unions, investment funds, insurance carriers.',
  '61': 'Educational Services - Schools, colleges, universities, training centers.',
  '71': 'Arts, Entertainment, and Recreation - Performing arts, museums, sports, gaming.',
  '56': 'Administrative and Support Services - Office admin, employment services, security.',
  '81': 'Other Services - Repair, personal care, religious, civic organizations.',
  '48-49': 'Transportation and Warehousing - Air, rail, water, truck transportation, warehousing.',
  '44-45': 'Retail Trade - Stores selling merchandise to consumers.',
  '62': 'Health Care and Social Assistance - Hospitals, clinics, nursing homes, social services.',
  '31-33': 'Manufacturing - Production of goods from raw materials.',
  '92': 'Public Administration - Government agencies and services.',
  '11': 'Agriculture, Forestry, Fishing and Hunting - Farms, ranches, forestry, fishing.',
  '72': 'Accommodation and Food Services - Hotels, restaurants, bars, catering.',
  '53': 'Real Estate and Rental and Leasing - Property rental, real estate agents.',
  '22': 'Utilities - Electric power, natural gas, water supply.',
  '23': 'Construction - Building construction, infrastructure, specialty trades.',
  '42': 'Wholesale Trade - Selling goods to retailers or businesses.',
  '21': 'Mining, Quarrying, and Oil and Gas Extraction - Resource extraction industries.',
}

export const AGENT_COMPANIES: Record<string, string> = {
  claude: 'Anthropic',
  copilot: 'GitHub / Microsoft',
  codex: 'OpenAI',
  cursor: 'Anysphere',
}

export const AGENT_STATS: Record<string, { repos: string; profServices: string; months: number; growthRank: string }> = {
  claude: { repos: '391K', profServices: '28%', months: 13, growthRank: '#1' },
  copilot: { repos: '247K', profServices: '25%', months: 14, growthRank: '#2' },
  codex: { repos: '249K', profServices: '22%', months: 14, growthRank: '#3' },
  cursor: { repos: '129K', profServices: '24%', months: 14, growthRank: '#4' },
}

export const KEY_FINDINGS = [
  {
    number: '01',
    title: 'Professional Services Dominates',
    description: 'NAICS sector 54 (Professional, Scientific, and Technical Services) leads adoption across all agents, representing 22-28% of repositories. This is expected as software development is a core activity in this sector.',
  },
  {
    number: '02',
    title: 'Information Sector Strong Second',
    description: 'NAICS sector 51 (Information) consistently ranks second across all agents, representing tech companies, publishers, and data processing organizations heavily invested in software development.',
  },
  {
    number: '03',
    title: 'Claude Code Shows Fastest Growth',
    description: 'Claude Code demonstrates the steepest adoption curve, particularly in late 2025, with January 2026 alone seeing 111,000+ new repositories — more than double Copilot\'s and Codex\'s monthly growth.',
  },
  {
    number: '04',
    title: 'Finance and Healthcare Accelerating',
    description: 'Sectors 52 (Finance) and 62 (Healthcare) show accelerating adoption rates, suggesting growing trust in AI coding tools for regulated industries.',
  },
]

export const INDUSTRY_EXAMPLES: Record<string, string[]> = {
  '54': ['Software consulting', 'Legal tech', 'Accounting tools', 'Engineering firms'],
  '51': ['SaaS platforms', 'Media companies', 'Data analytics', 'Telecom'],
  '52': ['Fintech', 'Banking apps', 'Insurance platforms', 'Trading tools'],
  '61': ['EdTech', 'LMS platforms', 'Online courses', 'University projects'],
  '71': ['Gaming', 'Streaming', 'Sports analytics', 'VR/AR'],
  '56': ['HR tech', 'Staffing platforms', 'Security services', 'Facility management'],
  '81': ['Repair services', 'Personal care apps', 'Civic organizations', 'Religious orgs'],
  '48-49': ['Logistics', 'Fleet management', 'Delivery apps', 'Supply chain'],
  '44-45': ['E-commerce', 'POS systems', 'Inventory management', 'Online marketplaces'],
  '62': ['Health records', 'Telemedicine', 'Clinical tools', 'Social services'],
  '31-33': ['IoT manufacturing', 'Quality control', 'Supply chain', 'Automation'],
  '92': ['Gov tech', 'Public records', 'Civic apps', 'Defense tools'],
  '11': ['AgriTech', 'Precision farming', 'Forestry management', 'Fisheries'],
  '72': ['Hotel booking', 'Restaurant POS', 'Food delivery', 'Travel tech'],
  '53': ['PropTech', 'Rental platforms', 'Real estate CRM', 'Property management'],
  '22': ['Smart grid', 'Energy management', 'Water systems', 'Power distribution'],
  '23': ['Project management', 'BIM tools', 'Contractor apps', 'Safety tracking'],
  '42': ['B2B marketplaces', 'Distribution tools', 'Wholesale platforms', 'Trade logistics'],
  '21': ['Mining tech', 'Oil & gas analytics', 'Resource mapping', 'Extraction tools'],
}
