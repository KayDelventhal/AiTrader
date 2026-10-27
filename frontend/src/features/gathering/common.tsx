import { useQuery } from '@tanstack/react-query'
import { api } from '../../client/api'
import type { GatheringConfig, GatheringDomain } from './types'

export function useGatheringConfig() {
  return useQuery({ queryKey: ['gathering-config'], queryFn: () => api<GatheringConfig>('/gathering/config'), refetchInterval: 15000 })
}

export function stamp(value: string | null | undefined) {
  if (!value) return 'Not recorded'
  return new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }).format(new Date(value)) + ' UTC'
}

export function publicationStamp(at: string | null, on?: string | null) {
  return on ? `${on} (date only)` : stamp(at)
}

export function utcInput(value: string) {
  return value ? new Date(value + ':00Z').toISOString() : undefined
}

export function DomainChecks({ domains, values, onChange, label = 'Research domains' }: { domains: GatheringDomain[]; values: string[]; onChange: (values: string[]) => void; label?: string }) {
  return <fieldset className="gathering-domain-checks"><legend>{label}</legend><div>{domains.map(domain => <label key={domain.id}><input type="checkbox" checked={values.includes(domain.id)} onChange={event => onChange(event.target.checked ? [...values, domain.id] : values.filter(id => id !== domain.id))}/><span>{domain.name}{!domain.enabled && <small>Inactive interest</small>}</span></label>)}</div></fieldset>
}
