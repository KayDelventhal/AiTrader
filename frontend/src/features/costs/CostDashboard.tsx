import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, History, Plus, Repeat2, ShieldCheck, Wallet } from 'lucide-react'
import { useWorkspace } from '../../app/context'
import { api, downloadJson } from '../../client/api'
import { Badge, Empty, Panel } from '../../components/common'
import { Dialog } from '../../components/ui/dialog'
import { date, euro } from '../../lib/format'
import { categoryLabels, ExpenseDialog, RecurringDialog, statusLabels } from './CostForms'
import type { CostEntry, CostSummary, PerformanceCostView } from './types'

const budgetLabels: Record<CostSummary['status'], string> = { OK: 'Within budget', WARNING: 'Near the limit', EXHAUSTED: 'Budget exhausted', OVER_BUDGET: 'Over budget', UNKNOWN_COST: 'Unknown costs' }

function costAmount(value: string | null) {
  if (value === null) return 'Unknown'
  return new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR', minimumFractionDigits: 2, maximumFractionDigits: 6 }).format(Number(value))
}

export function CostDashboard() {
  const { act } = useWorkspace()
  const [month, setMonth] = useState('')
  const [expenseOpen, setExpenseOpen] = useState(false)
  const [recurringOpen, setRecurringOpen] = useState(false)
  const [editing, setEditing] = useState<CostEntry | undefined>()
  const [history, setHistory] = useState<CostEntry | undefined>()
  const [stopping, setStopping] = useState<string | null>(null)
  const costs = useQuery({ queryKey: ['costs', month], queryFn: () => api<CostSummary>(`/costs${month ? `?month=${month}` : ''}`) })
  const report = costs.data
  const selectedMonth = month || report?.month || ''
  const used = report ? Number(report.confirmed_eur) + Number(report.estimated_eur) + Number(report.reserved_eur) + Number(report.carryover_reserved_eur) : 0
  const limit = Number(report?.limit_eur || 0)

  return <div className="cost-workspace">
    <div className="cost-section-heading"><div><span className="eyebrow">ACTUAL EXPENSES, EVEN DURING PAPER TRAINING</span><h2>Operating costs</h2><p>One shared budget across AI, search/news and market data.</p></div><div className="cost-toolbar"><label>Budget month<input type="month" value={selectedMonth} max={report?.current_month} min="2000-01" onChange={event => setMonth(event.target.value)}/></label>{report && <button className="button" onClick={() => downloadJson(`aitrader-costs-${report.month}.json`, report)}><Download size={15}/> Export cost ledger</button>}</div></div>
    {costs.isPending ? <Empty>Loading operating costs…</Empty> : costs.error ? <Empty><p>{costs.error.message}</p><button className="button" onClick={() => void costs.refetch()}>Retry cost ledger</button></Empty> : report && <>
      <div className="cost-budget-banner"><div><Wallet size={19}/><span>Monthly limit <strong>{euro(report.limit_eur)}</strong></span><Badge tone={report.status === 'OK' ? 'green' : 'amber'}>{budgetLabels[report.status]}</Badge></div><p>{report.has_unknown ? 'A charge is unresolved. Further paid work is blocked until its cost is known.' : report.status === 'OVER_BUDGET' || report.status === 'EXHAUSTED' ? 'Further paid reservations are blocked. Local charts and saved research remain available.' : 'Paid work must reserve its bounded cost before it starts. No external provider is active in this demo.'}</p><progress aria-label="Monthly budget used or committed" value={Math.min(used, limit || 1)} max={limit || 1}/><small>Calendar month in Europe/Berlin · historical months retain their recorded limits</small></div>
      <div className="stats-grid cost-stats"><div className="stat-card" data-testid="cost-confirmed"><div>Confirmed expenses</div><strong>{costAmount(report.confirmed_eur)}</strong><small>Recorded bills and reconciled usage</small></div><div className="stat-card" data-testid="cost-estimated"><div>Estimated expenses</div><strong>{costAmount(report.estimated_eur)}</strong><small>Incurred, awaiting final billing</small></div><div className="stat-card" data-testid="cost-reserved"><div>Reserved this month</div><strong>{costAmount(report.reserved_eur)}</strong><small>Committed, not booked as an expense</small></div><div className="stat-card" data-testid="cost-available"><div>Available for paid work</div><strong className={Number(report.available_eur) > 0 ? 'positive' : ''}>{costAmount(report.available_eur)}</strong><small>{report.has_unknown ? 'Blocked by unresolved costs' : Number(report.remaining_eur) < 0 ? `${costAmount(String(-Number(report.remaining_eur)))} over the limit` : 'After expenses and commitments'}</small></div></div>
      {Number(report.carryover_reserved_eur) > 0 && <div className="read-only-note"><History size={16}/><span>{costAmount(report.carryover_reserved_eur)} remains reserved for unresolved earlier-month work and reduces this month’s available budget.</span></div>}
      <div className="cost-main-grid"><Panel title="Cost ledger" action={report.can_manage ? <button className="button" onClick={() => { setEditing(undefined); setExpenseOpen(true) }}><Plus size={15}/> Record expense</button> : <Badge>Read only</Badge>}>
        {report.entries.length ? <div className="scroll-table"><table className="cost-ledger"><thead><tr><th>Expense</th><th>State</th><th>Amount</th><th>Actions</th></tr></thead><tbody>{report.entries.map(entry => <tr key={entry.id}><td><strong>{entry.provider}</strong><small>{entry.description}</small><small>{categoryLabels[entry.category]} · {entry.source === 'recurring' ? 'Monthly commitment' : entry.source === 'reservation' ? 'Provider reservation' : 'Manual record'}</small></td><td><Badge tone={entry.status === 'CONFIRMED' ? 'green' : entry.status === 'CANCELLED' ? '' : 'amber'}>{statusLabels[entry.status]}</Badge></td><td>{entry.status === 'RESERVED' ? <>{costAmount(entry.reserved_eur)}<small>Reserved</small></> : entry.status === 'CANCELLED' ? '—' : costAmount(entry.amount_eur)}</td><td><div className="cost-row-actions"><button className="button" aria-label={`View history: ${entry.description}`} onClick={() => setHistory(entry)}><History size={13}/> History</button>{report.can_manage && <button className="button" aria-label={`Update cost: ${entry.description}`} onClick={() => { setEditing(entry); setExpenseOpen(true) }}>Update</button>}</div></td></tr>)}</tbody></table></div> : <Empty><Wallet size={28}/><h3>No recorded costs this month</h3><p>The current fixture workflows make no paid calls. Record external bills here when you have them.</p></Empty>}
        {!report.can_manage && <p className="cost-panel-note">The owner can record bills, resolve uncertain charges and manage commitments.</p>}
      </Panel><Panel title="By provider & category">
        {report.breakdown.length ? <div className="cost-breakdown">{report.breakdown.map(item => <div key={`${item.provider}:${item.category}`}><div><strong>{item.provider}</strong><Badge tone="blue">{categoryLabels[item.category]}</Badge></div><dl><dt>Confirmed</dt><dd>{costAmount(item.confirmed_eur)}</dd><dt>Estimated</dt><dd>{costAmount(item.estimated_eur)}</dd><dt>Reserved</dt><dd>{costAmount(item.reserved_eur)}</dd></dl>{item.has_unknown && <Badge tone="amber">Unresolved charge</Badge>}</div>)}</div> : <Empty>Provider totals appear when a cost or commitment is recorded.</Empty>}
      </Panel></div>
      <Panel title="Monthly commitments" action={report.can_manage && selectedMonth === report.current_month ? <button className="button" onClick={() => setRecurringOpen(true)}><Repeat2 size={15}/> Add monthly commitment</button> : undefined}>
        <p className="cost-panel-note">Current recurring-charge settings, including stopped plans. Recording or stopping entries never purchases, renews or cancels a subscription with a provider.</p>
        {report.recurring.length ? <div className="recurring-list">{report.recurring.map(plan => <div key={plan.id}><div><strong>{plan.provider} · {plan.description}</strong><small>{categoryLabels[plan.category]} · from {plan.start_month}{plan.end_month ? ` · last budget month ${plan.end_month}` : ' · ongoing'}</small></div><span>{costAmount(plan.monthly_amount_eur)} / month</span>{plan.end_month ? <Badge>Future entries stopped</Badge> : report.can_manage && <button className="button" disabled={stopping !== null} onClick={async () => { setStopping(plan.id); await act(() => api(`/costs/recurring/${plan.id}/stop`, 'POST', { expected_revision: plan.revision, event_key: `stop-${plan.id}-${plan.revision}` }), 'Future budget entries stopped. The current commitment and external subscription are unchanged.'); setStopping(null) }}>{stopping === plan.id ? 'Stopping…' : 'Stop future entries'}</button>}</div>)}</div> : <Empty>No monthly commitments recorded.</Empty>}
      </Panel>
      <PerformanceCostImpact month={report.month}/>
      <div className="settings-note"><ShieldCheck size={18}/><p>Costs shown here belong to this app’s shared workspace. Charges elsewhere in a provider account are not automatically imported. Estimated amounts, FX assumptions and later billing corrections remain visible in each record.</p></div>
      <ExpenseDialog open={expenseOpen} month={report.month} entry={editing} onClose={() => { setExpenseOpen(false); setEditing(undefined) }}/>
      <RecurringDialog open={recurringOpen} month={report.current_month} onClose={() => setRecurringOpen(false)}/>
      <Dialog open={!!history} onOpenChange={open => { if (!open) setHistory(undefined) }} title="Cost record history" description="Earlier versions remain available when a charge is corrected or reconciled.">{history && <div className="cost-history"><h3>{history.provider}</h3><p>{history.description}</p><dl><dt>Original amount</dt><dd>{history.original_amount === null ? 'Unknown' : `${history.original_amount} ${history.currency}`}</dd><dt>EUR conversion</dt><dd>{history.fx_rate ? `${history.fx_rate} EUR per ${history.currency}` : history.currency === 'EUR' ? 'EUR billing' : 'Not available'}</dd><dt>FX reference</dt><dd>{history.fx_as_of ? new Date(history.fx_as_of).toLocaleString('en-GB', { timeZone: 'UTC' }) + ' UTC' : 'Not applicable'}</dd><dt>Pricing reference</dt><dd>{history.pricing_version}</dd><dt>Cost attribution</dt><dd>{history.run_id ? `Run ${history.run_id}` : history.strategy_id ? `Strategy version ${history.strategy_id}` : 'Shared workspace'}</dd></dl><div className="cost-history-events">{history.history.map(revision => <div key={revision.revision}><Badge>Revision {revision.revision}</Badge><time>{date(revision.created_at)} · {revision.actor_id}</time><p>{revision.note}</p>{typeof revision.payload.status === 'string' && <small>{revision.payload.status.replaceAll('_', ' ')}</small>}<small>Recorded expense: {costAmount(typeof revision.payload.amount_eur === 'string' ? revision.payload.amount_eur : null)}</small>{typeof revision.payload.original_amount === 'string' && typeof revision.payload.currency === 'string' && <small>Original billing: {revision.payload.original_amount} {revision.payload.currency}</small>}{typeof revision.payload.fx_rate === 'string' && typeof revision.payload.currency === 'string' && <small>Conversion: {revision.payload.fx_rate} EUR per {revision.payload.currency}</small>}</div>)}</div></div>}</Dialog>
    </>}
  </div>
}

function PerformanceCostImpact({ month }: { month: string }) {
  const performance = useQuery({ queryKey: ['performance-cost-impact', month], queryFn: () => api<PerformanceCostView>(`/performance/cost-impact?month=${month}`) })
  const result = performance.data
  return <Panel title="Trading results & operating expenses" eyebrow="LOCAL DEMO COMPARISON" action={<Badge tone="amber">Fictional trading</Badge>}>
    {performance.isPending ? <Empty>Loading the period comparison…</Empty> : performance.error ? <Empty><p>{performance.error.message}</p><button className="button" onClick={() => void performance.refetch()}>Retry comparison</button></Empty> : result && <div className="cost-performance">
      <p>Actual operating expenses are shown against your local demo account as an illustration. Demo gains cannot pay real bills; live trading performance is not available.</p>
      <div className="cost-performance-grid"><div><small>Realized demo P&L</small><strong>{costAmount(result.realized_pnl_eur)}</strong><span>After booked execution costs</span></div><div><small>Unrealized demo P&L</small><strong>{costAmount(result.unrealized_pnl_eur)}</strong><span>Shown separately from realized results</span></div><div><small>Illustrative result after expenses</small><strong>{result.illustrative_net_eur === null ? 'Unavailable' : costAmount(result.illustrative_net_eur)}</strong><span>Realized demo P&L minus shared incurred expenses</span></div></div>
      <div className="cost-scenario-summary"><span>Confirmed expenses <b>{costAmount(result.operating_confirmed_eur)}</b></span><span>Estimated expenses <b>{costAmount(result.operating_estimated_eur)}</b></span><span>Reservations, not deducted <b>{costAmount(result.reserved_eur)}</b></span></div>
      <p className="cost-valuation">{result.valuation_basis}</p>
      {result.notes.map(note => <p className="cost-valuation" key={note}>{note}</p>)}
    </div>}
  </Panel>
}
