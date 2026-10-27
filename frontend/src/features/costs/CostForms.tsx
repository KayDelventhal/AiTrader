import { useRef, useState } from 'react'
import { api } from '../../client/api'
import { useWorkspace } from '../../app/context'
import { Dialog } from '../../components/ui/dialog'
import type { CostCategory, CostEntry, CostStatus } from './types'

export const categoryLabels: Record<CostCategory, string> = { AI: 'AI analysis', SEARCH_NEWS: 'Search & news', MARKET_DATA: 'Market data' }
export const statusLabels: Record<CostStatus, string> = { CONFIRMED: 'Confirmed', ESTIMATED: 'Estimated', UNCERTAIN: 'Unknown charge', RESERVED: 'Reserved', CANCELLED: 'Cancelled' }

function useRequestKey() {
  const key = useRef('')
  return (_payload: unknown) => {
    // A lost response may hide a successful write. Keep this form's key even
    // when values change, so the server rejects an ambiguous duplicate.
    if (!key.current) key.current = crypto.randomUUID()
    return key.current
  }
}

export function ExpenseDialog({ month, entry, open, onClose }: { month: string; entry?: CostEntry; open: boolean; onClose: () => void }) {
  return <Dialog open={open} onOpenChange={value => { if (!value) onClose() }} title={entry ? 'Update cost record' : 'Record an operating expense'} description={entry ? 'Record a bill, correction or uncertain outcome. Earlier versions remain in the record history.' : 'Record an expense already incurred or an uncertain charge. This does not contact or pay a provider.'}>
    {open && <ExpenseForm month={month} entry={entry} onClose={onClose}/>}
  </Dialog>
}

function ExpenseForm({ month, entry, onClose }: { month: string; entry?: CostEntry; onClose: () => void }) {
  const { act, jobs, strategies, user } = useWorkspace()
  const requestKey = useRequestKey()
  const [provider, setProvider] = useState(entry?.provider || '')
  const [category, setCategory] = useState<CostCategory>(entry?.category || 'AI')
  const [description, setDescription] = useState(entry?.description || '')
  const [status, setStatus] = useState<Exclude<CostStatus, 'RESERVED'>>(entry && !['RESERVED', 'CANCELLED'].includes(entry.status) ? entry.status as Exclude<CostStatus, 'RESERVED'> : 'CONFIRMED')
  const [amount, setAmount] = useState(entry?.original_amount || '')
  const [currency, setCurrency] = useState(entry?.currency || 'EUR')
  const [fxRate, setFxRate] = useState(entry?.fx_rate || '')
  const [fxAt, setFxAt] = useState(new Date(entry?.fx_as_of || Date.now()).toISOString().slice(0, 16))
  const [pricing, setPricing] = useState(entry?.pricing_version || 'Manual invoice')
  const [note, setNote] = useState('')
  const [attribution, setAttribution] = useState<'shared' | 'run' | 'strategy'>('shared')
  const [attributionId, setAttributionId] = useState('')
  const [busy, setBusy] = useState(false)
  const ownedStrategies = strategies.filter(strategy => strategy.author_id === user.id)
  const needsAmount = status === 'CONFIRMED' || status === 'ESTIMATED'
  const hasAmount = amount !== '' && needsAmount
  const canCancel = entry && entry.source !== 'manual' && ['RESERVED', 'UNCERTAIN'].includes(entry.status)
  return <form className="cost-form" onSubmit={async event => {
    event.preventDefault()
    setBusy(true)
    const values = { status, amount: hasAmount ? amount : null, currency, fx_rate: currency !== 'EUR' && hasAmount ? fxRate : null, fx_as_of: currency !== 'EUR' && hasAmount ? `${fxAt}:00Z` : null, pricing_version: pricing }
    const payload = entry ? { ...values, expected_revision: entry.revision, note } : { ...values, month, provider, category, description, run_id: attribution === 'run' ? attributionId : null, strategy_id: attribution === 'strategy' ? attributionId : null }
    const success = await act(() => api(entry ? `/costs/${entry.id}/reconcile` : '/costs/entries', 'POST', { ...payload, [entry ? 'event_key' : 'idempotency_key']: requestKey(payload) }), entry ? 'Cost record updated. Earlier versions were retained.' : 'Operating expense recorded. No provider was contacted.')
    setBusy(false)
    if (success) onClose()
  }}>
    {!entry ? <><label>Provider<input required maxLength={80} value={provider} onChange={event => setProvider(event.target.value)} placeholder="Provider name"/></label><label>Cost category<select value={category} onChange={event => setCategory(event.target.value as CostCategory)}>{Object.entries(categoryLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Expense description<input required maxLength={300} value={description} onChange={event => setDescription(event.target.value)} placeholder="Invoice or usage description"/></label></> : <div className="cost-record-subject"><strong>{entry.provider}</strong><p>{entry.description} · {entry.month}</p></div>}
    <label>Cost certainty<select value={status} onChange={event => setStatus(event.target.value as Exclude<CostStatus, 'RESERVED'>)}><option value="CONFIRMED">Confirmed amount</option><option value="ESTIMATED">Estimated amount</option><option value="UNCERTAIN">Unknown or uncertain charge</option>{canCancel && <option value="CANCELLED">Cancelled — no charge</option>}</select></label>
    {status === 'UNCERTAIN' && <p className="cost-form-note">The charge is unknown and blocks further paid work until resolved. Choose Estimated amount if a usable estimate is available.</p>}
    {needsAmount && <div className="cost-form-grid"><label>Original amount<input type="number" min="0" max="100000" step="0.000001" required value={amount} onChange={event => setAmount(event.target.value)}/></label><label>Billing currency<input required pattern="[A-Z]{3}" maxLength={3} value={currency} onChange={event => setCurrency(event.target.value.toUpperCase())}/></label></div>}
    {currency !== 'EUR' && hasAmount && <div className="cost-form-grid"><label>EUR per 1 {currency}<input type="number" min="0.000001" step="0.000001" required value={fxRate} onChange={event => setFxRate(event.target.value)}/></label><label>FX reference time (UTC)<input type="datetime-local" required value={fxAt} onChange={event => setFxAt(event.target.value)}/></label></div>}
    <label>Pricing or invoice reference<input required maxLength={120} value={pricing} onChange={event => setPricing(event.target.value)} placeholder="Invoice number or dated price assumption"/></label>
    {!entry && <>
      <label>Assign cost to<select value={attribution} onChange={event => {
        const next = event.target.value as typeof attribution
        setAttribution(next)
        setAttributionId(next === 'run' ? jobs[0]?.id || '' : next === 'strategy' ? ownedStrategies[0]?.id || '' : '')
      }}><option value="shared">Shared workspace</option><option value="run">One saved analysis or backtest</option><option value="strategy">One strategy version</option></select></label>
      {attribution === 'run' && <label>Analysis or backtest<select required value={attributionId} onChange={event => setAttributionId(event.target.value)}>{!jobs.length && <option value="">No saved runs available</option>}{jobs.map(job => <option key={job.id} value={job.id}>{job.kind === 'backtest' ? 'Backtest' : 'Research'} · {job.id.slice(0, 8)} · {new Date(job.created_at).toLocaleDateString('en-GB', { timeZone: 'Europe/Berlin' })}</option>)}</select></label>}
      {attribution === 'strategy' && <label>Cost strategy version<select required value={attributionId} onChange={event => setAttributionId(event.target.value)}>{!ownedStrategies.length && <option value="">No owned strategy versions available</option>}{ownedStrategies.map(strategy => <option key={strategy.id} value={strategy.id}>{strategy.spec.name} · v{strategy.version}</option>)}</select></label>}
      <p className="cost-form-note">This charge is recorded once. Shared research remains a workspace expense; assigning it to one run or strategy does not duplicate the cost.</p>
    </>}
    {entry && <label>Reason for update<textarea required minLength={3} maxLength={500} rows={2} value={note} onChange={event => setNote(event.target.value)} placeholder="What changed, and what is the evidence?"/></label>}
    <p className="cost-form-note">Recorded bills may exceed the monthly limit. The ledger preserves the expense and prevents further paid reservations; it does not hide the bill.</p>
    {entry?.source === 'manual' && <p className="cost-form-note">To correct a manual bill that was not charged, enter a confirmed amount of zero and record the reason.</p>}
    <div className="dialog-actions"><button type="button" className="button" disabled={busy} onClick={onClose}>Cancel</button><button className="button primary" disabled={busy}>{busy ? 'Saving…' : entry ? 'Save cost update' : 'Record expense'}</button></div>
  </form>
}

export function RecurringDialog({ month, open, onClose }: { month: string; open: boolean; onClose: () => void }) {
  return <Dialog open={open} onOpenChange={value => { if (!value) onClose() }} title="Record a monthly commitment" description="Track an existing subscription or recurring charge in your budget. This does not subscribe to or activate a service.">
    {open && <RecurringForm month={month} onClose={onClose}/>}
  </Dialog>
}

function RecurringForm({ month, onClose }: { month: string; onClose: () => void }) {
  const { act } = useWorkspace()
  const requestKey = useRequestKey()
  const [provider, setProvider] = useState('')
  const [category, setCategory] = useState<CostCategory>('MARKET_DATA')
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [busy, setBusy] = useState(false)
  return <form className="cost-form" onSubmit={async event => {
    event.preventDefault(); setBusy(true)
    const payload = { provider, category, description, monthly_amount_eur: amount, start_month: month }
    const success = await act(() => api('/costs/recurring', 'POST', { ...payload, idempotency_key: requestKey(payload) }), 'Monthly commitment recorded. No subscription was purchased.')
    setBusy(false)
    if (success) onClose()
  }}>
    <label>Commitment provider<input required maxLength={80} value={provider} onChange={event => setProvider(event.target.value)}/></label>
    <label>Commitment category<select value={category} onChange={event => setCategory(event.target.value as CostCategory)}>{Object.entries(categoryLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    <label>Commitment description<input required maxLength={300} value={description} onChange={event => setDescription(event.target.value)}/></label>
    <label>Monthly commitment (EUR)<input type="number" min="0.000001" step="0.000001" required value={amount} onChange={event => setAmount(event.target.value)}/></label>
    <p className="cost-form-note">Starts in {month}. The amount is reserved once per month until you stop future renewals. Update each monthly record when the actual bill is known.</p>
    <div className="dialog-actions"><button type="button" className="button" disabled={busy} onClick={onClose}>Cancel</button><button className="button primary" disabled={busy}>{busy ? 'Saving…' : 'Save monthly commitment'}</button></div>
  </form>
}
