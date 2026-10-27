import { useState } from 'react'
import { Radar, ArrowRight, BookOpen, ShieldQuestion, Download, Library, Settings2, FlaskConical } from 'lucide-react'
import { useWorkspace } from '../../app/context'
import { api, downloadJson } from '../../client/api'
import { Badge, Panel, Empty } from '../../components/common'
import { date } from '../../lib/format'
import { RunHistory } from '../../components/RunHistory'
import { SourceLibrary } from '../gathering/SourceLibrary'
import { GatheringSetup } from '../gathering/GatheringSetup'
import '../gathering/gathering.css'

type ResearchView = 'library' | 'setup' | 'demo'

export function Research() {
  const [view, setView] = useState<ResearchView>(() => {
    const requested = new URLSearchParams(window.location.search).get('view')
    return requested === 'setup' ? 'setup' : requested === 'library' || requested === 'sources' ? 'library' : 'demo'
  })
  function selectView(next: ResearchView) {
    setView(next)
    const url = new URL(window.location.href)
    url.searchParams.set('view', next)
    window.history.replaceState(window.history.state, '', url)
  }
  return <><div className="page-heading compact"><div><span className="eyebrow">SIGNAL, WITH ITS SOURCES</span><h1>Research & events</h1><p>Collect evidence across domains and preserve how the available information changes.</p></div><Badge tone={view === 'demo' ? 'amber' : 'blue'}>{view === 'demo' ? 'SYNTHETIC SCENARIOS' : 'SOURCE RESEARCH'}</Badge></div><nav className="gathering-nav" aria-label="Research views"><button className={view === 'library' ? 'active' : ''} aria-pressed={view === 'library'} onClick={() => selectView('library')}><Library size={15}/> Source library</button><button className={view === 'setup' ? 'active' : ''} aria-pressed={view === 'setup'} onClick={() => selectView('setup')}><Settings2 size={15}/> Gathering setup</button><button className={view === 'demo' ? 'active' : ''} aria-pressed={view === 'demo'} onClick={() => selectView('demo')}><FlaskConical size={15}/> Demo research</button></nav>{view === 'library' ? <SourceLibrary/> : view === 'setup' ? <GatheringSetup/> : <DemoResearch/>}</>
}

function DemoResearch() {
  const { events, instruments, selected, select, jobs, act } = useWorkspace()
  const [domain, setDomain] = useState('All domains')
  const [chosen, setChosen] = useState(events[0]?.id)
  const event = events.find(e => e.id === chosen)
  const filtered = events.filter(e => domain === 'All domains' || e.domain === domain)
  const [runId, setRunId] = useState<string | undefined>()
  const researchJobs = jobs.filter(j => j.kind === 'research')
  const job = researchJobs.find(j => j.id === runId) || researchJobs[0]
  return <><div className="filter-row">{['All domains', ...new Set(events.map(e => e.domain))].map(d => <button className={domain === d ? 'filter-chip active' : 'filter-chip'} key={d} onClick={() => setDomain(d)}>{d}</button>)}</div><div className="research-layout"><div className="event-list">{filtered.map(e => <button className={`panel event-card ${chosen === e.id ? 'selected' : ''}`} key={e.id} onClick={() => setChosen(e.id)}><div className="event-top"><Badge tone="blue">{e.domain}</Badge><small>{date(e.available_at)}</small></div><h3>{e.title}</h3><p>{e.summary}</p><div className="event-bottom"><Badge tone={e.status === 'OBSERVED' ? 'amber' : ''}>{e.status}</Badge><span>{e.evidence.length} independent origin <ArrowRight size={14}/></span></div></button>)}</div><Panel title={event?.title || 'Select an event'} eyebrow="EVENT DETAIL · FIXTURE EVIDENCE">{event && <div className="event-detail"><div className="event-top"><Badge tone="amber">{event.claim_type}</Badge><span>Available {date(event.available_at)}</span></div><p className="lead-text">{event.summary}</p><h4>Potential transmission path</h4><div className="causal-chain">{event.mechanism.map((step, i) => <div key={step}><span>{String(i + 1).padStart(2, '0')}</span><p>{step}</p>{i < event.mechanism.length - 1 && <ArrowRight size={17}/>}</div>)}</div><h4>Connected instruments</h4><div className="strategy-tags">{event.instrument_ids.map(id => <Badge key={id}>{instruments.find(i => i.id === id)?.name || id}</Badge>)}</div><div className="counterargument"><ShieldQuestion size={20}/><div><h4>What could challenge this?</h4><p>{event.counterargument}</p></div></div><h4>Evidence trail</h4>{event.evidence.map(e => <div className="evidence-card" key={e.id}><BookOpen size={19}/><div><b>{e.title}</b><p>{e.publisher} · revision {e.revision} · {e.id}</p><small>{e.copies} copies grouped into {e.independent_origins} original source. Fictional fixture, not a real publication.</small></div></div>)}<div className="next-check"><span className="eyebrow">NEXT CHECK</span><p>{event.next_check}</p></div><button className="button" onClick={() => downloadJson(`aitrader-event-${event.id}.json`, event)}><Download size={15}/> Export event evidence</button></div>}</Panel></div><Panel title="Evidence review" eyebrow="DETERMINISTIC RESEARCH GRAPH"><div className="research-controls"><label>Review instrument<select value={selected} onChange={e => select(e.target.value)}>{instruments.map(i => <option key={i.id} value={i.id}>{i.symbol} · {i.name}</option>)}</select></label><button className="button primary" disabled={job?.status === 'RUNNING' || job?.status === 'PENDING'} onClick={() => void act(async () => { const queued = await api<{ job_id: string }>('/research-runs', 'POST', { instrument_id: selected }); setRunId(queued.job_id) }, 'Evidence review queued')}><Radar size={16}/> Run evidence review</button><small>LangGraph fixture workflow · no model calls · €0.00</small></div><RunHistory jobs={researchJobs} selectedId={job?.id} onSelect={setRunId}/>{job?.result && job.status === 'SUCCEEDED' ? <div className="research-result"><div className="workflow-steps">{job.result.steps.map((step, i) => <span key={step}><b>{i + 1}</b>{step}</span>)}</div><h3>{job.result.conclusion}</h3>{job.result.findings.map(f => <p key={f}>{f}</p>)}<p className="muted">Referenced evidence: {job.result.evidence_ids.join(', ') || 'None available'}</p></div> : job ? <Empty><Badge>{job.status}</Badge>{job.error || 'The review will appear here when complete.'}</Empty> : <Empty>Run a review to combine the available evidence and counterarguments. A lack of evidence is a valid result.</Empty>}</Panel></>
}
