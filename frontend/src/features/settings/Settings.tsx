import { useQuery } from '@tanstack/react-query'
import { Server, LockKeyhole, ShieldCheck } from 'lucide-react'
import { api, type SystemStatus } from '../../client/api'
import { Panel, Badge, Empty } from '../../components/common'
import { WorkspaceDefaults } from './WorkspaceDefaults'
import { CostDashboard } from '../costs/CostDashboard'
import { GatheringShortcut } from '../gathering/GatheringSetup'
import { useGatheringConfig } from '../gathering/common'

export function Settings() {
  const gathering = useGatheringConfig()
  const status = useQuery({ queryKey: ['status'], queryFn: () => api<SystemStatus>('/system-status') })
  return <>
    <div className="page-heading compact"><div><span className="eyebrow">RESEARCH SCOPE, COSTS AND CAPABILITIES</span><h1>Settings & system status</h1><p>Choose defaults for future work, control operating expenses, and inspect actual integration status.</p></div><Badge tone="green">LOCAL WORKSPACE</Badge></div>
    <div className="settings-summary workspace-settings-grid">
      <WorkspaceDefaults/>
      <Panel title="Current environment">
        <div className="setting-fact"><Server size={20}/><span>Application mode<strong>DEMO / private loopback</strong></span></div>
        <div className="setting-fact"><LockKeyhole size={20}/><span>Public feed collection<strong>{gathering.data ? gathering.data.settings.enabled && gathering.data.network_allowed ? 'Enabled for configured sources' : 'Paused' : 'Checking...'}</strong></span></div>
        <div className="setting-fact"><ShieldCheck size={20}/><span>Order execution<strong>Local fictional fills only</strong></span></div>
        <dl className="settings-dl"><dt>Language</dt><dd>English</dd><dt>Reporting currency</dt><dd>EUR</dd><dt>Display timezone</dt><dd>Europe/Berlin</dd><dt>Storage</dt><dd>{status.data?.database || 'Checking...'}</dd><dt>Background work</dt><dd>{status.data?.worker || 'Checking...'}</dd><dt>Fixture model calls</dt><dd>None</dd></dl>
      </Panel>
    </div>
    <GatheringShortcut/>
    <CostDashboard/>
    <Panel title="Integration readiness" eyebrow="NO IMPLIED VERIFICATION"><div className="service-list">{status.data?.services.map(service => <div className="service-row" key={service.name}><span className={`service-dot ${service.status === 'Ready' ? 'ready' : ''}`}/><div><h3>{service.name}</h3><p>{service.detail}</p></div><Badge tone={service.status === 'Ready' ? 'green' : service.status === 'Disabled' ? '' : 'amber'}>{service.status}</Badge></div>)}{status.error && <Empty>{status.error.message}</Empty>}</div></Panel>
    <div className="settings-note"><LockKeyhole size={18}/><p>Secrets remain in the server environment. Public feed collection has its own explicit switch. Paid model providers and external trading remain inactive; storing source evidence does not create real market-price coverage.</p></div>
  </>
}
