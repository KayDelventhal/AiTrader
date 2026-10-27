import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, ArrowRight, BookOpen, Download, ExternalLink, History, Upload } from 'lucide-react'
import { api, downloadJson } from '../../client/api'
import { Badge, Empty, Panel } from '../../components/common'
import { Dialog } from '../../components/ui/dialog'
import { ImportDialog } from './GatheringForms'
import { publicationStamp, stamp, useGatheringConfig, utcInput } from './common'
import type { GatheringConfig, GatheringDocumentDetail, GatheringDocumentPage, GatheringRevision } from './types'
import './gathering.css'

export function SourceLibrary() {
  const config = useGatheringConfig()
  if (config.isPending) return <Empty>Loading the source library...</Empty>
  if (config.error) return <Empty><p>{config.error.message}</p><button className="button" onClick={() => void config.refetch()}>Retry source library</button></Empty>
  return config.data && <LibraryContents config={config.data}/>
}

function LibraryContents({ config }: { config: GatheringConfig }) {
  const [domain, setDomain] = useState('')
  const [source, setSource] = useState('')
  const [query, setQuery] = useState('')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [knownBy, setKnownBy] = useState('')
  const [applied, setApplied] = useState('')
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState<string>()
  const [importOpen, setImportOpen] = useState(false)
  const [filterError, setFilterError] = useState('')
  const limit = 20
  const params = new URLSearchParams(applied)
  params.set('offset', String(offset)); params.set('limit', String(limit))
  const knownCutoff = new URLSearchParams(applied).get('known_by') || undefined
  const documents = useQuery({ queryKey: ['gathering-documents', applied, offset], queryFn: () => api<GatheringDocumentPage>(`/gathering/documents?${params}`), refetchInterval: knownCutoff ? false : 15000 })
  const page = documents.data
  return <div className="gathering-workspace">
    <div className="gathering-library-heading"><div><span className="eyebrow">PERSISTENT EVIDENCE LIBRARY</span><h2>Build context across domains</h2><p>Browse original source excerpts, publication dates and revision history. These records are evidence awaiting analysis, not verified market conclusions.</p></div>{config.can_manage && <button className="button" onClick={() => setImportOpen(true)}><Upload size={15}/> Import historical source</button>}</div>
    <Panel title="Timeline filters" action={<History size={17}/>}>
      <form className="gathering-filter-form" onSubmit={event => {
        event.preventDefault()
        if (from && to && from > to) { setFilterError('The publication start date must be on or before the end date.'); return }
        setFilterError('')
        const next = new URLSearchParams()
        if (domain) next.set('domain_id', domain)
        if (source) next.set('source_id', source)
        if (query.trim()) next.set('q', query.trim())
        if (from) next.set('date_from', from + 'T00:00:00Z')
        if (to) next.set('date_to', to + 'T23:59:59.999999Z')
        if (knownBy) next.set('known_by', utcInput(knownBy)!)
        setApplied(next.toString()); setOffset(0)
      }}>
        <div className="gathering-filter-grid"><label>Research domain<select value={domain} onChange={e => setDomain(e.target.value)}><option value="">All research domains</option>{config.domains.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Collection source<select value={source} onChange={e => setSource(e.target.value)}><option value="">All sources and manual imports</option>{config.sources.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Search stored sources<input value={query} onChange={e => setQuery(e.target.value)} maxLength={200} placeholder="Title or source text"/></label></div>
        <div className="gathering-filter-grid"><label>Published from<input type="date" value={from} onChange={e => setFrom(e.target.value)}/></label><label>Published through<input type="date" value={to} onChange={e => setTo(e.target.value)}/></label><label>Known by this app (UTC)<input type="datetime-local" value={knownBy} onChange={e => setKnownBy(e.target.value)}/></label></div>
        <div className="gathering-filter-footer"><p>A publication can be old while its first observation is recent. The knowledge cutoff selects only revisions actually recorded by that time; imported history is never backdated.</p><button className="button primary">Apply timeline filters</button><button className="button" type="button" onClick={() => { setDomain(''); setSource(''); setQuery(''); setFrom(''); setTo(''); setKnownBy(''); setApplied(''); setOffset(0); setFilterError('') }}>Reset filters</button></div>
        {filterError && <p className="form-error" role="alert">{filterError}</p>}
      </form>
    </Panel>
    {knownCutoff && <div className="gathering-notice"><History size={17}/><p>Showing the latest recorded revision available by {stamp(knownCutoff)}. Later changes are excluded from this view.</p></div>}
    {documents.isPending ? <Empty>Loading stored source records...</Empty> : documents.error ? <Empty><p>{documents.error.message}</p><button className="button" onClick={() => void documents.refetch()}>Retry documents</button></Empty> : page && <>
      <div className="gathering-results-bar"><span>{page.total} stored document{page.total === 1 ? '' : 's'} match these filters</span><small>Newest publication first · unknown publication dates remain explicit</small></div>
      {page.items.length ? <div className="gathering-document-list">{page.items.map(document => <button className="panel gathering-document-card" key={document.id} onClick={() => setSelected(document.id)}><div className="gathering-document-meta"><span>{document.revision.publisher}</span><Badge tone={document.source_kind === 'MANUAL' ? 'amber' : 'blue'}>{document.source_kind === 'MANUAL' ? 'Manual historical import' : 'Public feed'}</Badge><Badge>Revision {document.revision.revision}</Badge></div><h3>{document.revision.title}</h3><p>{document.revision.content || 'This feed supplied a headline and link without an excerpt.'}</p><div className="gathering-tags">{document.revision.domains.map(item => <span key={item.id}>{item.name}</span>)}</div><div className="gathering-document-dates"><span>Published <b>{publicationStamp(document.revision.published_at, document.revision.published_on)}</b></span><span>First seen <b>{stamp(document.first_seen_at)}</b></span><span>Revision available <b>{stamp(document.revision.available_at)}</b></span><ArrowRight size={16}/></div></button>)}</div> : <Empty><BookOpen size={30}/><h3>No source records in this view</h3><p>Configure a public feed or import an older publication. If filters are active, widen them to see more records.</p><a className="button" href="/research?view=setup">Configure gathering</a></Empty>}
      <div className="gathering-pagination"><button className="button" disabled={offset === 0 || documents.isFetching} onClick={() => setOffset(Math.max(0, offset - limit))}><ArrowLeft size={14}/> Previous</button><span>{page.total ? `${offset + 1}–${Math.min(offset + page.items.length, page.total)} of ${page.total}` : '0 results'}</span><button className="button" disabled={offset + page.items.length >= page.total || documents.isFetching} onClick={() => setOffset(offset + limit)}>Next <ArrowRight size={14}/></button></div>
    </>}
    {selected && <DocumentDialog id={selected} knownBy={knownCutoff} onClose={() => setSelected(undefined)}/>}
    {importOpen && <ImportDialog config={config} onClose={() => setImportOpen(false)} onImported={id => { setApplied(''); setOffset(0); setDomain(''); setSource(''); setQuery(''); setFrom(''); setTo(''); setKnownBy(''); setSelected(id) }}/>}
  </div>
}

function DocumentDialog({ id, knownBy, onClose }: { id: string; knownBy?: string; onClose: () => void }) {
  const detail = useQuery({ queryKey: ['gathering-document', id, knownBy], queryFn: () => api<GatheringDocumentDetail>(`/gathering/documents/${id}${knownBy ? '?known_by=' + encodeURIComponent(knownBy) : ''}`) })
  const [selectedRevision, setSelectedRevision] = useState<number>()
  const data = detail.data
  const revision = data?.revisions.find(item => item.revision === selectedRevision) || data?.document.revision
  return <Dialog open onOpenChange={open => { if (!open) onClose() }} title="Stored source and revisions" description="Inspect the publisher's material and the version available to the application at each observation time.">
    {detail.isPending ? <Empty>Loading source history...</Empty> : detail.error ? <Empty>{detail.error.message}</Empty> : data && revision && <div className="gathering-document-detail"><div className="gathering-document-meta"><Badge tone="blue">{data.document.source_kind === 'RSS' ? 'Public feed record' : 'Manual source record'}</Badge><Badge>Revision {revision.revision}</Badge></div><h3>{revision.title}</h3><p>{revision.publisher}</p><a className="button" href={revision.url} target="_blank" rel="noopener noreferrer"><ExternalLink size={14}/> Open original publication</a><dl className="gathering-source-facts"><dt>Published</dt><dd>{publicationStamp(revision.published_at, revision.published_on)}</dd><dt>Event occurred</dt><dd>{stamp(revision.occurred_at)}</dd><dt>Publisher updated</dt><dd>{stamp(revision.source_updated_at)}</dd><dt>First seen by this app</dt><dd>{stamp(data.document.first_seen_at)}</dd><dt>This revision recorded</dt><dd>{stamp(revision.recorded_at)}</dd><dt>This revision available</dt><dd>{stamp(revision.available_at)}</dd></dl><div className="gathering-tags">{revision.domains.map(domain => <span key={domain.id}>{domain.name}</span>)}</div><p className="gathering-form-note">{revision.attribution}</p><div className="gathering-source-text">{revision.content || 'No excerpt was supplied with this source record.'}</div>{revision.note && <p className="gathering-import-note">Import note: {revision.note}</p>}<h4>Revision history</h4><div className="gathering-revision-list">{data.revisions.map(item => <RevisionButton key={item.id} revision={item} selected={revision.id === item.id} onSelect={() => setSelectedRevision(item.revision)}/>)}</div><p className="gathering-form-note">Source records and domain assignments are evidence for later review. They do not establish market causation. The application preserves earlier versions instead of replacing their content.</p><button className="button" onClick={() => downloadJson(`aitrader-source-${id}.json`, data)}><Download size={14}/> Export source history</button></div>}
  </Dialog>
}

function RevisionButton({ revision, selected, onSelect }: { revision: GatheringRevision; selected: boolean; onSelect: () => void }) {
  return <button className={selected ? 'selected' : ''} onClick={onSelect}><span>Revision {revision.revision}</span><small>Observed {stamp(revision.recorded_at)}</small><p>{revision.title}</p></button>
}
