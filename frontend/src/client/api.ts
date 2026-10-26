export type Instrument = { id: string; symbol: string; name: string; sector: string; currency: string; color: string; price: string; change_pct: number; as_of: number; watched: boolean; sparkline: number[] }
export type Bar = { time: number; open: number; high: number; low: number; close: number; volume: number }
export type Point = { time: number; value: number }
export type MarketData = { instrument_id: string; bars: Bar[]; indicators: Record<string, Point[]>; as_of: number; first_time: number; last_time: number; total_bars: number }
export type Evidence = { id: string; publisher: string; title: string; revision: number; copies: number; independent_origins: number; available_at: string }
export type ResearchEvent = { id: string; title: string; domain: string; status: string; severity: string; summary: string; mechanism: string[]; counterargument: string; next_check: string; evidence: Evidence[]; available_at: string; instrument_ids: string[]; claim_type: string }
export type Spec = { name: string; hypothesis: string; instrument_id: string; fast: number; slow: number; size: number; fees_bps: number; slippage_bps: number; status?: string }
export type Strategy = { id: string; strategy_id: string; version: number; author_id: string; created_at: string; spec: Spec }
export type BacktestResult = { engine: string; return_pct: number; max_drawdown_pct: number; closed_trades: number; win_rate_pct: number | null; final_equity: number; stress_return_pct: number; equity: Point[]; benchmark: Point[]; assumptions: string[]; orders: { time: number; signal_time: number; side: string; quantity: number; price: number; fees: number }[]; snapshot_hash: string }
export type ResearchResult = { conclusion: string; findings: string[]; counterarguments: string[]; evidence_ids: string[]; steps: string[]; provider: string; model_calls: number }
export type Job = { id: string; kind: string; status: string; created_at: string; result: (BacktestResult & ResearchResult) | null; error: string | null }
export type Account = { id: string; cash: string; killed: number; revision: number; positions: Record<string, { quantity: number; cost_basis: string; realized_pnl: string }> }
export type Proposal = { id: string; status: string; digest: string; expires_at: string; payload: { symbol: string; side: string; quantity: number; price: string; fee: string; reference_time: number; fill_assumption: string }; fill: unknown }
export type AuditEvent = { id: number; actor_id: string; action: string; created_at: string; object_id: string }
export type Annotation = { id: string; price: string; as_of: number }
export type Notice = { id: string; message: string; read: number; created_at: string }
export type SystemStatus = { mode: string; database: string; external_requests: boolean; live_enabled: boolean; worker: string; services: { name: string; status: string; detail: string }[] }
export type User = { id: string; name: string; csrf: string }

let csrf = ''
export function setCsrf(value: string) { csrf = value }
export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`/api/v1${path}`, { method, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', ...(csrf ? { 'X-CSRF-Token': csrf } : {}) }, body: body === undefined ? undefined : JSON.stringify(body) })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(typeof data.detail === 'string' ? data.detail : data.detail ? 'Please check the form values.' : `Request failed (${response.status})`)
  }
  return response.json()
}
export function downloadJson(name: string, value: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }))
  const a = document.createElement('a'); a.href = url; a.download = name; a.click(); URL.revokeObjectURL(url)
}
