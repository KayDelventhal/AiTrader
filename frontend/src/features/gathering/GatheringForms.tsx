import { useState } from 'react'
import { useWorkspace } from '../../app/context'
import { api } from '../../client/api'
import { Dialog } from '../../components/ui/dialog'
import { DomainChecks, utcInput } from './common'
import type { GatheringConfig, GatheringDomain, GatheringImportResult, GatheringSource } from './types'

export function DomainDialog({ domain, onClose }: { domain?: GatheringDomain; onClose: () => void }) {
  const { act } = useWorkspace()
  const [name, setName] = useState(domain?.name || '')
  const [description, setDescription] = useState(domain?.description || '')
  const [keywords, setKeywords] = useState(domain?.keywords.join(', ') || '')
  const [enabled, setEnabled] = useState(domain?.enabled ?? true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  return <Dialog open onOpenChange={open => { if (!open) onClose() }} title={domain ? 'Edit research domain' : 'Add research domain'} description="A domain can be a company, sector, region or broader economic theme.">
    <form className="gathering-form" onSubmit={async event => {
      event.preventDefault()
      const words = [...new Set(keywords.split(',').map(word => word.trim()).filter(Boolean))]
      if (words.length > 40 || words.some(word => word.length > 80)) { setError('Use up to 40 keywords, each at most 80 characters.'); return }
      setError(''); setBusy(true)
      const ok = await act(() => api(`/gathering/domains${domain ? '/' + domain.id : ''}`, domain ? 'PUT' : 'POST', { name: name.trim(), description, keywords: words, enabled, ...(domain ? { expected_revision: domain.revision } : {}) }), 'Research domain saved.')
      setBusy(false); if (ok) onClose()
    }}>
      <label>Domain name<input value={name} onChange={e => setName(e.target.value)} required minLength={2} maxLength={100}/></label>
      <label>Domain description<textarea value={description} onChange={e => setDescription(e.target.value)} rows={3} maxLength={1000} placeholder="What developments and indirect influences matter here?"/></label>
      <label>Keywords and related entities<input value={keywords} onChange={e => setKeywords(e.target.value)} placeholder="chips, export controls, energy supply"/><small>Comma-separated research vocabulary. Keywords do not discard feed items or automatically establish relevance.</small></label>
      <label className="gathering-check"><input type="checkbox" checked={enabled} onChange={e => setEnabled(e.target.checked)}/><span>Active research interest</span></label>
      <p className="gathering-form-note">Inactive domains are excluded from new feed runs. Collection pauses when every assigned domain is inactive. Existing documents and historical associations remain unchanged.</p>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="dialog-actions"><button className="button" type="button" onClick={onClose}>Cancel</button><button className="button primary" disabled={busy}>{busy ? 'Saving...' : 'Save research domain'}</button></div>
    </form>
  </Dialog>
}

export function SourceDialog({ config, source, onClose }: { config: GatheringConfig; source?: GatheringSource; onClose: () => void }) {
  const { act } = useWorkspace()
  const available = config.catalog.filter(item => source?.catalog_key === item.key || !config.sources.some(saved => saved.catalog_key === item.key))
  const [key, setKey] = useState(source?.catalog_key || available[0]?.key || '')
  const [domains, setDomains] = useState<string[]>(source?.domain_ids || [])
  const [interval, setInterval] = useState(source?.interval_minutes || 60)
  const [enabled, setEnabled] = useState(source?.enabled ?? false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const item = config.catalog.find(entry => entry.key === key)
  return <Dialog open onOpenChange={open => { if (!open) onClose() }} title={source ? 'Edit collection source' : 'Add collection source'} description="Select a supported public feed and the research domains it may inform.">
    <form className="gathering-form" onSubmit={async event => {
      event.preventDefault()
      if (!domains.length) { setError('Assign at least one research domain.'); return }
      setError(''); setBusy(true)
      const ok = await act(() => api(`/gathering/sources${source ? '/' + source.id : ''}`, source ? 'PUT' : 'POST', { domain_ids: domains, interval_minutes: interval, enabled, ...(source ? { expected_revision: source.revision } : { catalog_key: key }) }), 'Collection source saved.')
      setBusy(false); if (ok) onClose()
    }}>
      <label>Public feed<select value={key} onChange={e => setKey(e.target.value)} required disabled={!!source}>{available.map(entry => <option key={entry.key} value={entry.key}>{entry.name}</option>)}</select></label>
      {item && <div className="gathering-source-reference"><strong>{item.publisher}</strong><p>{item.description}</p><a href={item.reference_url || item.url} target="_blank" rel="noopener noreferrer">Publisher feed information</a><small>{item.url}</small></div>}
      <DomainChecks domains={config.domains} values={domains} onChange={setDomains} label="Domains this source may inform"/>
      <label>Check every (minutes)<input type="number" value={interval} onChange={e => setInterval(Number(e.target.value))} required min={15} max={10080}/><small>15 minutes to 7 days. Runs while the local application is running.</small></label>
      <label className="gathering-check"><input type="checkbox" checked={enabled} onChange={e => setEnabled(e.target.checked)}/><span>Enable this source for collection</span></label>
      <p className="gathering-form-note">The workspace collection switch must also be on, with at least one assigned domain active. New runs include only active domains. Feed entries retain their original links and excerpts; collection makes no LLM calls. Domain assignments describe configured coverage, not verified causal relevance.</p>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="dialog-actions"><button className="button" type="button" onClick={onClose}>Cancel</button><button className="button primary" disabled={busy || !key}>{busy ? 'Saving...' : 'Save collection source'}</button></div>
    </form>
  </Dialog>
}

export function ImportDialog({ config, onClose, onImported }: { config: GatheringConfig; onClose: () => void; onImported: (id: string) => void }) {
  const { act } = useWorkspace()
  const [key] = useState(() => crypto.randomUUID())
  const [publisher, setPublisher] = useState('')
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [text, setText] = useState('')
  const [published, setPublished] = useState('')
  const [publishedOn, setPublishedOn] = useState('')
  const [publicationPrecision, setPublicationPrecision] = useState<'unknown' | 'date' | 'datetime'>('unknown')
  const [occurred, setOccurred] = useState('')
  const [note, setNote] = useState('')
  const [domains, setDomains] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  return <Dialog open onOpenChange={open => { if (!open) onClose() }} title="Import historical source" description="Preserve an older publication or source excerpt with its provenance. This records evidence, not a verified market event.">
    <form className="gathering-form" onSubmit={async event => {
      event.preventDefault()
      if (!domains.length) { setError('Assign at least one research domain.'); return }
      setError(''); setBusy(true)
      let imported: GatheringImportResult | undefined
      const ok = await act(async () => { imported = await api<GatheringImportResult>('/gathering/imports', 'POST', { idempotency_key: key, publisher, url, title, text, domain_ids: domains, published_at: publicationPrecision === 'datetime' ? utcInput(published) : undefined, published_on: publicationPrecision === 'date' ? publishedOn : undefined, occurred_at: utcInput(occurred), note }) }, 'Historical source imported with its actual observation time.')
      setBusy(false); if (ok && imported) { onImported(imported.document_id); onClose() }
    }}>
      <div className="gathering-form-grid"><label>Publisher<input value={publisher} onChange={e => setPublisher(e.target.value)} required minLength={2} maxLength={120}/></label><label>Publication URL<input type="url" value={url} onChange={e => setUrl(e.target.value)} required maxLength={2000} placeholder="https://..." pattern="https://.*"/></label></div>
      <label>Publication title<input value={title} onChange={e => setTitle(e.target.value)} required minLength={3} maxLength={500}/></label>
      <label>Source text or excerpt<textarea value={text} onChange={e => setText(e.target.value)} rows={5} required minLength={10} maxLength={50000}/><small>Paste material you can store. The application does not fetch this URL or generate a replacement article.</small></label>
      <label>Publication date precision<select value={publicationPrecision} onChange={e => { setPublicationPrecision(e.target.value as typeof publicationPrecision); setPublished(''); setPublishedOn('') }}><option value="unknown">Unknown</option><option value="date">Date only</option><option value="datetime">Exact date and time</option></select><small>Keep the precision the source provides. Do not invent a publication time for a date-only archive.</small></label>
      <div className="gathering-form-grid">{publicationPrecision === 'datetime' && <label>Published at (UTC)<input type="datetime-local" required value={published} onChange={e => setPublished(e.target.value)}/></label>}{publicationPrecision === 'date' && <label>Publication date only<input type="date" required value={publishedOn} onChange={e => setPublishedOn(e.target.value)}/><small>Use when the publication gives a date but no exact time.</small></label>}<label>Event occurred at (UTC)<input type="datetime-local" value={occurred} onChange={e => setOccurred(e.target.value)}/><small>Optional; only when supported by the publication.</small></label></div>
      <DomainChecks domains={config.domains} values={domains} onChange={setDomains}/>
      <label>Import note<textarea value={note} onChange={e => setNote(e.target.value)} maxLength={1000} rows={2} placeholder="Archive location, excerpt boundaries or date uncertainty"/></label>
      <p className="gathering-form-note">First seen and revision availability are recorded now. An old publication date does not mean this application knew the information then. Historical backfills remain identifiable in the timeline.</p>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="dialog-actions"><button className="button" type="button" onClick={onClose}>Cancel</button><button className="button primary" disabled={busy}>{busy ? 'Importing...' : 'Import source'}</button></div>
    </form>
  </Dialog>
}
