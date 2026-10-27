import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiClientError, setCsrf } from './api'

afterEach(() => { vi.unstubAllGlobals(); setCsrf('') })

describe('API request and error boundary', () => {
  it('sends the exact approval payload with the current CSRF token', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'FILLED' })))
    vi.stubGlobal('fetch', fetch)
    setCsrf('session-csrf')
    await api('/proposals/id/approve', 'POST', { digest: 'exact-digest' })
    expect(fetch).toHaveBeenCalledWith('/api/v1/proposals/id/approve', expect.objectContaining({
      method: 'POST', credentials: 'same-origin', body: '{"digest":"exact-digest"}',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': 'session-csrf' },
    }))
  })

  it('preserves actionable server errors and correlation identifiers', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      code: 'APPROVAL_EXPIRED', detail: 'Create a new proposal.', request_id: 'server-id',
    }), { status: 409 })))
    await expect(api('/proposals/id/approve', 'POST', {})).rejects.toMatchObject({
      name: 'ApiClientError', status: 409, code: 'APPROVAL_EXPIRED', requestId: 'server-id', message: 'Create a new proposal.',
    })
  })

  it('handles a non-JSON failure without exposing its body', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('private upstream debug page', {
      status: 503, headers: { 'X-Request-ID': 'proxy-id' },
    })))
    const error = await api('/jobs').catch(e => e)
    expect(error).toBeInstanceOf(ApiClientError)
    expect(error).toMatchObject({ status: 503, code: 'REQUEST_FAILED', requestId: 'proxy-id', message: 'Request failed (503)' })
  })
})
