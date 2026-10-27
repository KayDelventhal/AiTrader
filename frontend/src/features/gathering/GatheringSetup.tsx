import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Clock3, Database, Pause, Play, Plus, RefreshCw, Rss, Tags } from 'lucide-react'
import { useWorkspace } from '../../app/context'
import { api } from '../../client/api'
import { Badge, Empty, Panel } from '../../components/common'
import { DomainDialog, SourceDialog } from './GatheringForms'
import { stamp, useGatheringConfig } from './common'
import type { GatheringConfig, GatheringDomain, GatheringRun, GatheringSource } from './types'
import './gathering.css'

export function GatheringShortcut() {
  const config = useGatheringConfig()
  const active = !!config.data?.settings.enabled && config.data.network_allowed
  return <Panel title="Research gathering" eyebrow="DOMAINS, SOURCES AND HISTORY" action={<Badge tone={active ? 'green' : 'amber'}>{active ? 'Collection enabled' : 'Collection paused'}</Badge>}>
    <div className="gathering-shortcut"><div><p>Choose research domains, assign public sources and set collection intervals. Older publications can be imported into the source library.</p>{config.data && <small>{config.data.domains.length} domains · {config.data.sources.filter(source => source.enabled).length} enabled sources · no LLM calls</small>}{config.error && <p>{config.error.message}</p>}</div><a className="button" href="/research?view=setup">Configure gathering <ArrowRight size={15}/></a></div>
  </Panel>
}

export function GatheringSetup() {
  const config = useGatheringConfig()
  if (config.isPending) return <Empty>Loading gathering configuration...</Empty>
  if (config.error) return <Empty><p>{config.error.message}</p><button className="button" onClick={() => void config.refetch()}>Retry gathering configuration</button></Empty>
  return config.data && <SetupContents config={config.data}/>
}

function SetupContents({ config }: { config: GatheringConfig }) {
  const { act } = useWorkspace()
  const [domainOpen, setDomainOpen] = useState(false)
  const [editingDomain, setEditingDomain] = useState<GatheringDomain>()
  const [sourceOpen, setSourceOpen] = useState(false)
  const [editingSource, setEditingSource] = useState<GatheringSource>()
  const [busy, setBusy] = useState('')
  const active = config.settings.enabled && config.network_allowed
  const hasActiveDomain = (source: GatheringSource) => source.domain_ids.some(id => config.domains.some(domain => domain.id === id && domain.enabled))
  const runs = useQuery({ queryKey: ['gathering-runs'], queryFn: () => api<GatheringRun[]>('/gathering/runs'), refetchInterval: query => query.state.data?.some(run => ['QUEUED', 'RUNNING'].includes(run.status)) ? 1500 : 15000 })
  return <div className="gathering-workspace">
    <div className="gathering-switch-panel"><div className="gathering-switch-copy"><span className="eyebrow">PUBLIC SOURCE COLLECTION</span><h2>{active ? 'Keep building your research history' : 'Set the scope, then start collecting'}</h2><p>Retrieve public feed headlines, source excerpts and links. Sources are stored for later analysis; this workflow makes no paid model calls.</p><small>{config.settings.schedule_note}</small></div><div className="gathering-switch-action"><Badge tone={active ? 'green' : 'amber'}>{active ? 'Collection enabled' : 'Collection paused'}</Badge>{config.can_manage && <button className={`button ${config.settings.enabled ? '' : 'primary'}`} disabled={!!busy || (!config.network_allowed && !config.settings.enabled)} onClick={async () => { setBusy('settings'); await act(() => api('/gathering/settings', 'PUT', { expected_revision: config.settings.revision, enabled: !config.settings.enabled }), config.settings.enabled ? 'Public feed collection paused. Saved sources remain available.' : 'Public feed collection enabled for your configured sources.'); setBusy('') }}>{config.settings.enabled ? <Pause size={15}/> : <Play size={15}/>} {config.settings.enabled ? 'Pause collection' : 'Enable collection'}</button>}</div></div>
    {!config.network_allowed && <div className="gathering-notice"><Database size={17}/><p>Public network collection is disabled for this runtime. You can still configure domains, inspect saved documents and import source text. No feed request will be sent.</p></div>}
    {!config.can_manage && <div className="read-only-note"><span>Shared research configuration is visible to both members. Only the owner can change domains, sources or collection settings.</span></div>}
    <div className="gathering-setup-grid"><Panel title="Research domains" eyebrow="COMPANIES, SECTORS AND GLOBAL THEMES" action={config.can_manage ? <button className="button" onClick={() => { setEditingDomain(undefined); setDomainOpen(true) }}><Plus size={14}/> Add domain</button> : <Badge>Read only</Badge>}>
      <p className="gathering-panel-note">Keep broad developments alongside company interests. A domain is a topic you want to observe; it does not grant trading permission.</p>
      <div className="gathering-domain-list">{config.domains.map(domain => <article key={domain.id}><div className="gathering-item-heading"><Tags size={17}/><h3>{domain.name}</h3><Badge tone={domain.enabled ? 'green' : ''}>{domain.enabled ? 'Active interest' : 'Inactive'}</Badge></div>{domain.description && <p>{domain.description}</p>}<div className="gathering-tags">{domain.keywords.map(keyword => <span key={keyword}>{keyword}</span>)}</div>{config.can_manage && <button className="button" aria-label={`Edit domain: ${domain.name}`} onClick={() => { setEditingDomain(domain); setDomainOpen(true) }}>Edit domain</button>}</article>)}</div>
      {!config.domains.length && <Empty>Add a company, sector or global research theme to begin.</Empty>}
    </Panel><Panel title="Collection sources" eyebrow="SUPPORTED PUBLIC FEEDS" action={config.can_manage && <button className="button" disabled={!config.domains.length || config.sources.length >= config.catalog.length} onClick={() => { setEditingSource(undefined); setSourceOpen(true) }}><Plus size={14}/> Add source</button>}>
      <p className="gathering-panel-note">Each feed is collected once and can inform several domains. Assignments indicate configured coverage; they do not establish that every item affects each company.</p>
      <div className="gathering-source-list">{config.sources.map(source => <article key={source.id}><div className="gathering-item-heading"><Rss size={17}/><h3>{source.name}</h3><Badge tone={source.active_run_id ? 'blue' : source.enabled && hasActiveDomain(source) ? 'green' : 'amber'}>{source.active_run_id ? 'Collecting' : !hasActiveDomain(source) ? 'No active domains' : source.enabled ? 'Enabled' : 'Paused'}</Badge></div><a className="gathering-source-url" href={source.url} target="_blank" rel="noopener noreferrer">{source.publisher}</a><div className="gathering-tags">{source.domain_ids.map(id => <span key={id}>{config.domains.find(domain => domain.id === id)?.name || id}{config.domains.find(domain => domain.id === id)?.enabled === false ? ' (inactive)' : ''}</span>)}</div><dl className="gathering-source-facts"><dt>Check interval</dt><dd>{source.interval_minutes} minutes</dd><dt>Last checked</dt><dd>{stamp(source.last_checked_at)}</dd><dt>Last success</dt><dd>{stamp(source.last_success_at)}</dd><dt>Next due</dt><dd>{active && source.enabled && hasActiveDomain(source) ? stamp(source.next_due_at) : 'Paused'}</dd></dl>{!hasActiveDomain(source) && <p className="gathering-panel-note">Activate an assigned domain to resume collection. Existing source history is preserved.</p>}{source.last_error && <p className="gathering-source-error">{source.last_error}</p>}{config.can_manage && <div className="gathering-item-actions"><button className="button" aria-label={`Edit source: ${source.name}`} onClick={() => { setEditingSource(source); setSourceOpen(true) }}>Edit source</button><button className="button" aria-label={`Collect now: ${source.name}`} disabled={!active || !source.enabled || !hasActiveDomain(source) || !!source.active_run_id || !!busy} onClick={async () => { setBusy(source.id); await act(() => api(`/gathering/sources/${source.id}/collect`, 'POST', {}), 'Collection queued. The run log will report what was retrieved.'); setBusy('') }}><RefreshCw size={13}/> Collect now</button></div>}</article>)}</div>
      {!config.sources.length && <Empty><Rss size={27}/><h3>No collection sources yet</h3><p>Add a public feed, assign its domains and enable collection. Source availability and errors are shown here.</p></Empty>}
      {config.sources.length > 0 && !active && <p className="gathering-panel-note">Enable workspace collection and the individual source to use Collect now or scheduled checks.</p>}
    </Panel></div>
    <Panel title="Collection run log" eyebrow="ACTUAL RETRIEVAL RESULTS" action={<Clock3 size={17}/>}>
      {runs.isPending ? <Empty>Loading collection runs...</Empty> : runs.error ? <Empty>{runs.error.message}</Empty> : runs.data?.length ? <div className="gathering-run-list">{runs.data.slice(0, 12).map(run => <article key={run.id}><div><h3>{config.sources.find(source => source.id === run.source_id)?.name || 'Collection source'}</h3><small>{stamp(run.created_at)} · {run.trigger === 'MANUAL' ? 'Manual request' : 'Scheduled check'}</small><p>{Object.entries(run.counts).map(([key, count]) => `${key.replaceAll('_', ' ')}: ${count}`).join(' · ') || (['QUEUED', 'RUNNING'].includes(run.status) ? 'Waiting for retrieval results' : 'No stored changes')}</p>{run.error && <p className="gathering-source-error">{run.error}</p>}</div><Badge tone={run.status === 'SUCCEEDED' ? 'green' : ['QUEUED', 'RUNNING'].includes(run.status) ? 'blue' : 'amber'}>{run.status}</Badge></article>)}</div> : <Empty>No collection attempts yet. The first run will appear here with its outcome.</Empty>}
    </Panel>
    {domainOpen && <DomainDialog key={editingDomain?.id || 'new'} domain={editingDomain} onClose={() => setDomainOpen(false)}/>}
    {sourceOpen && <SourceDialog key={editingSource?.id || 'new'} config={config} source={editingSource} onClose={() => setSourceOpen(false)}/>}
  </div>
}
