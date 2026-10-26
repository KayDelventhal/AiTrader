import type { ReactNode } from 'react'
import { ArrowUpRight, LoaderCircle } from 'lucide-react'
export function Badge({ children, tone = '' }: { children: ReactNode; tone?: string }) { return <span className={`badge ${tone}`}>{children}</span> }
export function Panel({ title, eyebrow, action, children, className = '' }: { title?: string; eyebrow?: string; action?: ReactNode; children: ReactNode; className?: string }) { return <section className={`panel ${className}`}>{title && <div className="panel-heading"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h2>{title}</h2></div>{action}</div>}{children}</section> }
export function Empty({ children }: { children: ReactNode }) { return <div className="empty-state">{children}</div> }
export function Loading() { return <div className="empty-state"><LoaderCircle className="spin" size={22}/> Loading workspace…</div> }
export function Sparkline({ values, color = '#64d6b0' }: { values: number[]; color?: string }) { const min = Math.min(...values); const range = Math.max(...values) - min || 1; return <svg className="sparkline" viewBox="0 0 120 36" aria-hidden="true"><path d={values.map((v, i) => `${i ? 'L' : 'M'}${i * 120 / Math.max(1, values.length - 1)},${32 - (v - min) / range * 28}`).join(' ')} stroke={color} fill="none" strokeWidth="1.8"/></svg> }
export function TextLink({ children, onClick }: { children: ReactNode; onClick: () => void }) { return <button className="text-link" onClick={onClick}>{children}<ArrowUpRight size={14}/></button> }
