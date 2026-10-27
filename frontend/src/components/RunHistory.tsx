import { Download, Fingerprint } from 'lucide-react'
import { useWorkspace } from '../app/context'
import { api, downloadJson, type Job, type InputSnapshot } from '../client/api'
import { Badge } from './common'
import { date } from '../lib/format'

export function RunHistory({ jobs, selectedId, onSelect }: { jobs: Job[]; selectedId?: string; onSelect: (id: string) => void }) {
  const { act, strategies, instruments } = useWorkspace()
  if (!jobs.length) return null
  const job = jobs.find(j => j.id === selectedId) || jobs[0]
  function subject(run: Job) {
    const strategy = strategies.find(s => s.id === run.input.strategy_version_id)
    const instrument = instruments.find(i => i.id === run.input.instrument_id)
    return strategy ? `${strategy.spec.name} · v${strategy.version}` : instrument?.name || run.input.instrument_id || 'Unknown instrument'
  }
  return <section className="run-history" aria-label="Saved run history">
    <div className="run-history-heading"><Fingerprint size={17}/><div><h3>Saved runs</h3><p>Each new run keeps the exact inputs captured when you submitted it.</p></div></div>
    <label>Inspect a saved run<select value={job.id} onChange={e => onSelect(e.target.value)}>{jobs.map(j => <option key={j.id} value={j.id}>{subject(j)} · {date(j.created_at)} · {j.id.slice(0, 8)} · {j.status}</option>)}</select></label>
    <p className="run-subject">Selected result: {subject(job)}</p>
    <div className="run-history-detail"><Badge tone={job.input.snapshot_hash ? 'green' : 'amber'}>{job.input.snapshot_hash ? 'Frozen inputs' : 'Legacy run'}</Badge><span>{job.input.snapshot_hash ? `SHA-256 ${job.input.snapshot_hash.slice(0, 16)}…` : 'This older run predates input snapshots.'}</span>{job.input.snapshot_hash && <button className="button" onClick={() => void act(async () => { const snapshot = await api<InputSnapshot>(`/jobs/${job.id}/snapshot`); downloadJson(`aitrader-inputs-${job.id}.json`, snapshot) })}><Download size={14}/> Export inputs</button>}</div>
  </section>
}
