import { BookOpen, Download, ExternalLink } from 'lucide-react'

export function Help() {
  return <>
    <div className="page-heading compact"><div><span className="eyebrow">FUNCTIONS, DATA AND BACKGROUND WORK</span><h1>Help & guide</h1><p>Detailed instructions for this local AiTrader version, including its current limits.</p></div></div>
    <div className="filter-row" style={{ gap: 12, marginBottom: 16 }}>
      <a className="button" href="/help/user-guide.html" target="_blank" rel="noreferrer"><ExternalLink size={16}/> Open full guide</a>
      <a className="button" href="/help/user-guide.html" download="AiTrader-user-guide.html"><Download size={16}/> Download HTML guide</a>
      <span className="muted"><BookOpen size={15}/> The downloaded guide works offline.</span>
    </div>
    <iframe title="AiTrader user guide" src="/help/user-guide.html" sandbox="allow-same-origin" style={{ width: '100%', height: 'calc(100vh - 235px)', minHeight: 520, border: '1px solid #223241', borderRadius: 12, background: '#0e151e' }}/>
  </>
}
