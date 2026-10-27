import type { components } from './schema'

// Generated from validated FastAPI response contracts.
export type Instrument = components['schemas']['InstrumentView']
export type Bar = components['schemas']['BarView']
export type Point = components['schemas']['Point']
export type MarketData = components['schemas']['MarketDataView']
export type Evidence = components['schemas']['EvidenceView']
export type ResearchEvent = components['schemas']['EventView']
export type Strategy = components['schemas']['StrategyView']
export type BacktestResult = components['schemas']['BacktestResult']
export type ResearchResult = components['schemas']['ResearchResult']
export type BacktestJob = components['schemas']['BacktestJob']
export type ResearchJob = components['schemas']['ResearchJob']
export type Account = components['schemas']['AccountView']
export type Proposal = components['schemas']['ProposalView']
export type AuditEvent = components['schemas']['AuditView']
export type Annotation = components['schemas']['AnnotationView']
export type Notice = components['schemas']['NotificationView']
export type SystemStatus = components['schemas']['SystemStatusView']
export type User = components['schemas']['UserView']
export type InputSnapshot = components['schemas']['InputSnapshot']
export type RunCost = components['schemas']['RunCostView']
export type ApiProblem = components['schemas']['ErrorResponse']
export type Spec = Omit<components['schemas']['StrategyDetails'], 'status'> & { status?: 'draft' }
export type Job = BacktestJob | ResearchJob

export class ApiClientError extends Error {
  constructor(message: string, public status: number, public code: string, public requestId?: string) {
    super(message)
    this.name = 'ApiClientError'
  }
}

let csrf = ''
export function setCsrf(value: string) { csrf = value }
export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`/api/v1${path}`, { method, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', ...(csrf ? { 'X-CSRF-Token': csrf } : {}) }, body: body === undefined ? undefined : JSON.stringify(body) })
  if (!response.ok) {
    const data: Partial<ApiProblem> = await response.json().catch(() => ({}))
    throw new ApiClientError(typeof data.detail === 'string' ? data.detail : `Request failed (${response.status})`, response.status, data.code || 'REQUEST_FAILED', data.request_id || response.headers.get('X-Request-ID') || undefined)
  }
  return response.json()
}
export function downloadJson(name: string, value: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }))
  const a = document.createElement('a'); a.href = url; a.download = name; a.click(); URL.revokeObjectURL(url)
}
