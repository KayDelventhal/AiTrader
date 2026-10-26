import { useState, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useRouterState } from '@tanstack/react-router'
import { Activity, LayoutDashboard, ChartCandlestick, FlaskConical, Radar, Wallet, Settings2, Bell, Search, ArrowRight, LogOut, Check, X, ShieldCheck, ChevronDown, Menu } from 'lucide-react'
import { api, setCsrf, type User, type Instrument, type ResearchEvent, type Strategy, type Job, type Account, type Proposal, type Notice } from '../client/api'
import { WorkspaceContext } from './context'
import { Badge, Loading } from '../components/common'
import { Overview } from './Overview'
import { Terminal } from '../features/terminal/Terminal'
import { Strategies } from '../features/strategies/Strategies'
import { Research } from '../features/research/Research'
import { Portfolio } from '../features/portfolio/Portfolio'
import { Settings } from '../features/settings/Settings'

const navigation = [{ path: '/', label: 'Overview', icon: LayoutDashboard }, { path: '/terminal', label: 'Terminal', icon: ChartCandlestick }, { path: '/strategies', label: 'Strategy lab', icon: FlaskConical }, { path: '/research', label: 'Research & events', icon: Radar }, { path: '/portfolio', label: 'Portfolio & approvals', icon: Wallet }, { path: '/settings', label: 'Settings & status', icon: Settings2 }]

export function App() {
  const qc = useQueryClient()
  const navigateTo = useNavigate()
  const path = useRouterState({ select: state => state.location.pathname })
  const [user, setUser] = useState<User | null>(null)
  const [checking, setChecking] = useState(true)
  const [selected, select] = useState('DEMO_NOVA')
  const [toast, setToast] = useState<{ text: string; error: boolean } | null>(null)
  const [search, setSearch] = useState('')
  const [showNotices, setShowNotices] = useState(false)
  const [mobileNav, setMobileNav] = useState(false)
  useEffect(() => { api<User>('/auth/me').then(u => { setCsrf(u.csrf); setUser(u) }).catch(() => {}).finally(() => setChecking(false)) }, [])
  useEffect(() => { if (!toast) return; const t = setTimeout(() => setToast(null), 7000); return () => clearTimeout(t) }, [toast])
  const enabled = !!user
  const instruments = useQuery({ queryKey: ['instruments'], queryFn: () => api<Instrument[]>('/instruments'), enabled })
  const events = useQuery({ queryKey: ['events'], queryFn: () => api<ResearchEvent[]>('/events'), enabled })
  const strategies = useQuery({ queryKey: ['strategies'], queryFn: () => api<Strategy[]>('/strategies'), enabled })
  const jobs = useQuery({ queryKey: ['jobs'], queryFn: () => api<Job[]>('/jobs'), enabled, refetchInterval: query => query.state.data?.some(j => ['RUNNING', 'PENDING'].includes(j.status)) ? 1500 : false })
  const accounts = useQuery({ queryKey: ['accounts'], queryFn: () => api<Account[]>('/accounts'), enabled })
  const proposals = useQuery({ queryKey: ['proposals'], queryFn: () => api<Proposal[]>('/proposals'), enabled })
  const notices = useQuery({ queryKey: ['notifications'], queryFn: () => api<Notice[]>('/notifications'), enabled, refetchInterval: 15000 })
  async function refresh() { await qc.invalidateQueries() }
  async function act(work: () => Promise<unknown>, success?: string) { try { await work(); await refresh(); if (success) setToast({ text: success, error: false }); return true } catch (error) { setToast({ text: (error as Error).message, error: true }); return false } }
  function navigate(p: string) { void navigateTo({ to: p }); setMobileNav(false); setSearch('') }
  if (checking) return <div className="login-screen"><Loading/></div>
  if (!user) return <Login onLogin={u => { setCsrf(u.csrf); qc.clear(); setUser(u) }}/>
  const page = navigation.find(n => n.path === path) || navigation[0]
  const pending = proposals.data?.filter(p => p.status === 'AWAITING_APPROVAL' && new Date(p.expires_at) > new Date()).length || 0
  const error = [instruments, events, strategies, jobs, accounts, proposals].find(q => q.isError)?.error
  const loading = [instruments, events, strategies, jobs, accounts, proposals].some(q => q.isLoading)
  return <WorkspaceContext.Provider value={{ user, instruments: instruments.data || [], events: events.data || [], strategies: strategies.data || [], jobs: jobs.data || [], account: accounts.data?.[0], proposals: proposals.data || [], selected, select, refresh, act, navigate }}>
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? 'open' : ''}`}>
        <a className="brand" href="/" onClick={e => { e.preventDefault(); navigate('/') }}><span className="brand-symbol"><Activity size={22}/></span><span>ai<span className="brand-light">trader</span><small>RESEARCH WORKBENCH</small></span></a>
        <div className="workspace-label"><span className="workspace-dot">W</span><span>Personal workspace<small>Private · 2 members</small></span><ChevronDown size={14}/></div>
        <span className="nav-label">WORKSPACE</span>
        <nav>{navigation.slice(0, 5).map(item => <button key={item.path} className={path === item.path ? 'nav-item active' : 'nav-item'} onClick={() => navigate(item.path)}><item.icon size={18}/><span>{item.label}</span>{item.path === '/portfolio' && pending > 0 && <span className="nav-count">{pending}</span>}</button>)}</nav>
        <div className="sidebar-bottom"><div className="environment-card"><span className="status-dot"/> Demo environment<strong>Explore with confidence</strong><p>Fictional data. Local simulation.<br/>No external orders.</p><button className="text-link" onClick={() => navigate('/settings')}>View system status <ArrowRight size={13}/></button></div><button className={path === '/settings' ? 'nav-item active' : 'nav-item'} onClick={() => navigate('/settings')}><Settings2 size={18}/> Settings & status</button><div className="user-card"><span className="avatar">{user.name.split(' ').map(n => n[0]).join('')}</span><div>{user.name}<small>Demo researcher</small></div><button className="icon-button" aria-label="Sign out" onClick={() => void act(async () => { await api('/auth/logout', 'POST'); setUser(null); setCsrf(''); qc.clear() })}><LogOut size={16}/></button></div></div>
      </aside>
      <div className="main-shell">
        <header className="topbar"><div className="breadcrumb"><button className="icon-button mobile-menu" aria-label="Toggle navigation" onClick={() => setMobileNav(!mobileNav)}><Menu size={20}/></button><span>Workspace</span><span className="slash">/</span><strong>{page.label}</strong></div><div className="topbar-actions"><div className="search-wrap"><Search size={15}/><input aria-label="Search instruments" placeholder="Search instruments…" value={search} onChange={e => setSearch(e.target.value)}/>{search && <div className="search-results">{instruments.data?.filter(i => `${i.symbol} ${i.name}`.toLowerCase().includes(search.toLowerCase())).map(i => <button key={i.id} onClick={() => { select(i.id); navigate('/terminal') }}><b>{i.symbol}</b> {i.name}<ArrowRight size={14}/></button>)}{!instruments.data?.some(i => `${i.symbol} ${i.name}`.toLowerCase().includes(search.toLowerCase())) && <p>No matching instrument.</p>}</div>}</div><Badge tone="amber">DEMO</Badge><button className="icon-button notification-button" aria-label="Notifications" onClick={() => setShowNotices(!showNotices)}><Bell size={18}/>{notices.data?.some(n => !n.read) && <span/>}</button></div></header>
        {showNotices && <div className="notification-popover"><h3>Notifications</h3>{notices.data?.length ? notices.data.map(n => <button key={n.id} onClick={() => void act(() => api(`/notifications/${n.id}/read`, 'POST'))}><span>{n.message}</span>{n.read ? <Check size={15}/> : <Badge>New</Badge>}</button>) : <p>No notifications yet. Run a research review to create one.</p>}</div>}
        <main>{error ? <div className="error-banner" role="alert">{error.message}<button onClick={() => void refresh()}>Retry</button></div> : loading ? <Loading/> : path === '/terminal' ? <Terminal/> : path === '/strategies' ? <Strategies/> : path === '/research' ? <Research/> : path === '/portfolio' ? <Portfolio/> : path === '/settings' ? <Settings/> : <Overview/>}</main>
        <footer><span><span className="status-dot"/> Local demo · fictional market data</span><span>EUR · Europe/Berlin <span className="footer-divider">|</span> Live execution disabled <ShieldCheck size={12}/></span></footer>
      </div>
    </div>
    {toast && <div className={`toast ${toast.error ? 'error' : ''}`} role={toast.error ? 'alert' : 'status'}>{toast.error ? <X size={18}/> : <Check size={18}/>}<span>{toast.text}</span><button className="icon-button" aria-label="Dismiss message" onClick={() => setToast(null)}><X size={15}/></button></div>}
  </WorkspaceContext.Provider>
}

function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [username, setUsername] = useState('owner')
  const [password, setPassword] = useState('local-demo-owner')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  return <div className="login-screen"><div className="login-art"><div className="brand"><span className="brand-symbol"><Activity size={26}/></span><span>aitrader</span></div><Badge tone="green">YOUR PRIVATE RESEARCH WORKBENCH</Badge><h1>From market noise<br/>to considered decisions.</h1><p>Explore evidence. Test your assumptions.<br/>Keep every decision in your hands.</p><div className="login-grid"><SparkDecoration/></div><small>Research first. Execution by explicit approval.</small></div><div className="login-form"><Badge tone="amber">LOCAL DEMO</Badge><h2>Welcome to your workspace</h2><p>A working research environment, with fictional data and no external connections.</p><form onSubmit={async e => { e.preventDefault(); setBusy(true); setError(''); try { onLogin(await api<User>('/auth/login', 'POST', { username, password })) } catch (err) { setError((err as Error).message) } finally { setBusy(false) } }}><label>Demo account<select value={username} onChange={e => { setUsername(e.target.value); setPassword(e.target.value === 'owner' ? 'local-demo-owner' : 'local-demo-partner') }}><option value="owner">Alex Morgan · Owner</option><option value="partner">Sam Taylor · Partner</option></select></label><label>Password<input type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)}/></label>{error && <div className="error-banner" role="alert">{error}</div>}<button className="button primary" disabled={busy} type="submit">{busy ? 'Signing in…' : 'Open demo workspace'}<ArrowRight size={17}/></button></form><div className="login-note"><ShieldCheck size={20}/><span>Demo credentials are prefilled for this loopback-only preview. All prices, events, and balances are fictional.</span></div></div></div>
}
function SparkDecoration() { return <svg viewBox="0 0 480 140" aria-hidden="true"><defs><linearGradient id="lineFade" x1="0" y1="0" x2="1" y2="0"><stop stopColor="#296e60"/><stop offset="1" stopColor="#77e8bf"/></linearGradient></defs><path d="M0 120 L25 105 L45 112 L65 80 L90 95 L115 73 L145 90 L180 60 L205 70 L235 45 L260 58 L285 20 L310 35 L340 18 L360 42 L390 25 L420 38 L450 8 L480 18" stroke="url(#lineFade)" fill="none" strokeWidth="2"/></svg> }
