import { createContext, useContext } from 'react'
import type { User, Instrument, ResearchEvent, Strategy, Job, Account, Proposal } from '../client/api'
export type Workspace = { user: User; instruments: Instrument[]; events: ResearchEvent[]; strategies: Strategy[]; jobs: Job[]; account?: Account; proposals: Proposal[]; selected: string; select: (id: string) => void; refresh: () => Promise<void>; act: (work: () => Promise<unknown>, success?: string) => Promise<boolean>; navigate: (path: string) => void }
export const WorkspaceContext = createContext<Workspace>(null!)
export const useWorkspace = () => useContext(WorkspaceContext)
