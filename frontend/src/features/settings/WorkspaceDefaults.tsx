import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Globe2, Save, ShieldCheck } from 'lucide-react'
import { useWorkspace } from '../../app/context'
import { api } from '../../client/api'
import { Badge, Empty, Panel } from '../../components/common'

import type { components } from '../../client/schema'
import { horizonLabels } from '../../lib/horizon'

export type WorkspaceSettings = components['schemas']['WorkspaceSettingsView']
export type Horizon = WorkspaceSettings['horizon']

export function WorkspaceDefaults() {
  const settings = useQuery({ queryKey: ['workspace-settings'], queryFn: () => api<WorkspaceSettings>('/workspace/settings') })
  return <Panel title="Research defaults & spending limit" eyebrow="SHARED WORKSPACE SETTINGS" action={<Globe2 size={18}/> }>
    {settings.isPending ? <Empty>Loading workspace settings…</Empty> : settings.error ? <Empty><p>{settings.error.message}</p><button className="button" onClick={() => void settings.refetch()}>Retry settings</button></Empty> : settings.data && <DefaultsForm key={settings.data.revision} saved={settings.data}/>}
  </Panel>
}

function DefaultsForm({ saved }: { saved: WorkspaceSettings }) {
  const { act } = useWorkspace()
  const queryClient = useQueryClient()
  const [markets, setMarkets] = useState(saved.markets)
  const [horizon, setHorizon] = useState(saved.horizon)
  const initialLimit = saved.monthly_limit_eur.includes('.') ? saved.monthly_limit_eur.replace(/0+$/, '').replace(/\.$/, '') : saved.monthly_limit_eur
  const [limit, setLimit] = useState(initialLimit)
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState('')

  function toggleMarket(market: 'US' | 'EU') {
    setMarkets(previous => previous.includes(market) ? previous.filter(m => m !== market) : [...previous, market])
  }

  return <form className="workspace-defaults-form" onSubmit={async event => {
    event.preventDefault()
    if (!markets.length) { setFormError('Select at least one market.'); return }
    setFormError('')
    setBusy(true)
    await act(async () => {
      const updated = await api<WorkspaceSettings>('/workspace/settings', 'PUT', {
        expected_revision: saved.revision, markets, horizon, monthly_limit_eur: limit, warning_pct: saved.warning_pct,
      })
      queryClient.setQueryData(['workspace-settings'], updated)
    }, 'Workspace defaults saved. Existing strategies and runs keep their original settings.')
    setBusy(false)
  }}>
    {!saved.can_manage && <div className="read-only-note"><ShieldCheck size={16}/><span>Shared settings are visible to both members. Only the owner can change them.</span></div>}
    <fieldset disabled={!saved.can_manage || busy}>
      <legend>Markets to observe</legend>
      <div className="market-choices">
        <label className={`market-choice ${markets.includes('US') ? 'selected' : ''}`}><input type="checkbox" checked={markets.includes('US')} onChange={() => toggleMarket('US')}/><span><strong>United States</strong><small>US equity listings</small></span></label>
        <label className={`market-choice ${markets.includes('EU') ? 'selected' : ''}`}><input type="checkbox" checked={markets.includes('EU')} onChange={() => toggleMarket('EU')}/><span><strong>Europe</strong><small>European equity listings</small></span></label>
      </div>
      <p className="form-help">These choices set the observation scope. Real market feeds and listing selection are still pending.</p>
      <div className="workspace-input-grid">
        <label>Default research horizon<select value={horizon} onChange={event => setHorizon(event.target.value as Horizon)}>{Object.entries(horizonLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><small>Applies to new strategies and research runs.</small></label>
        <label>Monthly operating limit (EUR)<input type="number" min="0" max="10000" step="0.01" required value={limit} onChange={event => setLimit(event.target.value)}/><small>One shared limit for AI, search/news and market data.</small></label>
      </div>
    </fieldset>
    <div className="settings-policy"><ShieldCheck size={17}/><p>Budget increases require an explicit save. Profits never raise the limit automatically. Saving settings does not activate paid providers or trading.</p></div>
    {formError && <p className="form-error" role="alert">{formError}</p>}
    <div className="settings-form-footer"><Badge tone="blue">Revision {saved.revision}</Badge>{saved.can_manage && <button className="button primary" disabled={busy}><Save size={15}/>{busy ? 'Saving…' : 'Save workspace defaults'}</button>}</div>
  </form>
}
