import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createRootRoute, createRoute, createRouter, RouterProvider } from '@tanstack/react-router'
import { App } from './app/App'
import './styles.css'
import './responsive.css'

const root = createRootRoute({ component: App })
const routes = ['/', '/terminal', '/strategies', '/research', '/portfolio', '/settings'].map(path => createRoute({ getParentRoute: () => root, path, component: () => null }))
const router = createRouter({ routeTree: root.addChildren(routes) })
const client = new QueryClient({ defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } } })
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={client}><RouterProvider router={router}/></QueryClientProvider></React.StrictMode>)
