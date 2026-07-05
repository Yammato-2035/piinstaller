import { describe, expect, it, vi, beforeEach } from 'vitest'
import { loadDevDashboard } from './loadDevDashboard'

vi.mock('../../api', () => ({
  fetchApi: vi.fn(),
  getApiBase: () => '',
  normalizeApiBaseUrl: (s: string) => s,
}))

vi.mock('./isTauri', () => ({
  isTauriRuntime: () => false,
  invokeTauriWorkspaceScan: vi.fn(),
}))

import { fetchApi } from '../../api'

describe('loadDevDashboard', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }))
  })

  it('uses runtime_api when status endpoint returns 200', async () => {
    const dashboard = { backend_running: true, runtime_gate: { passed: true, status: 'green' } }
    vi.mocked(fetchApi).mockImplementation(async (path: string) => {
      if (path === '/health' || path === '/api/version') {
        return { ok: true, json: async () => ({ status: 'ok' }) } as Response
      }
      if (path.includes('/status')) {
        return { ok: true, json: async () => ({ dashboard }) } as Response
      }
      if (path.includes('/modules')) {
        return { ok: true, json: async () => ({ modules: [] }) } as Response
      }
      if (path.includes('/roadmap')) {
        return {
          ok: true,
          json: async () => ({
            roadmap: { areas: [{ id: 'diagnostics', title_de: 'Diagnostik', status: 'yellow', milestones: [] }] },
          }),
        } as Response
      }
      return { ok: true, json: async () => ({}) } as Response
    })

    const result = await loadDevDashboard('frontend_runtime_source=dev')
    expect(result.source).toBe('runtime_api')
    expect(result.apiReachable).toBe(true)
    expect(result.localApiReachable).toBe(true)
    expect(result.capabilities.runtimeTests).toBe(true)
    const roadmap = result.dashboard?.roadmap as Record<string, unknown>
    expect(Array.isArray(roadmap?.areas)).toBe(true)
    expect((roadmap?.areas as unknown[]).length).toBeGreaterThan(0)
  })

  it('falls back to unavailable when api and tauri and snapshot fail', async () => {
    vi.mocked(fetchApi).mockImplementation(async (path: string) => {
      if (path === '/health' || path === '/api/version') {
        throw new Error('offline')
      }
      throw new Error('offline')
    })
    const result = await loadDevDashboard('')
    expect(result.apiReachable).toBe(false)
    expect(result.localApiReachable).toBe(false)
    expect(result.dashboard).not.toBeNull()
    const rg = result.dashboard?.runtime_gate as Record<string, unknown>
    expect(rg.passed).toBe(false)
    expect(result.metaPrompt).toBeTruthy()
  })

  it('classifies api timeout as backend hanging timeout', async () => {
    vi.mocked(fetchApi).mockImplementation(async (path: string) => {
      if (path === '/health' || path === '/api/version') {
        throw Object.assign(new Error('timeout'), { name: 'AbortError' })
      }
      throw Object.assign(new Error('timeout'), { name: 'AbortError' })
    })
    const result = await loadDevDashboard('')
    expect(result.apiReachable).toBe(false)
    expect(result.source).toBe('unavailable')
    expect(result.offlineReason).toBe('backend_hanging_timeout')
  })

  it('sets localApiReachable when health/version ok but dev-dashboard blocked', async () => {
    vi.mocked(fetchApi).mockImplementation(async (path: string) => {
      if (path === '/health' || path === '/api/version') {
        return { ok: true, json: async () => ({ status: 'ok' }) } as Response
      }
      if (path.includes('/status')) {
        return {
          ok: false,
          status: 404,
          json: async () => ({ code: 'DEVELOPER_CAPABILITY_REQUIRED' }),
        } as Response
      }
      throw new Error('offline')
    })
    const result = await loadDevDashboard('')
    expect(result.localApiReachable).toBe(true)
    expect(result.apiReachable).toBe(false)
    expect(result.offlineReason).toBe('developer_token_required')
    expect(result.source).toBe('limited_live')
    expect(result.localApiReachable).toBe(true)
    expect(result.apiReachable).toBe(false)
    const rg = result.dashboard?.runtime_gate as Record<string, unknown>
    expect(rg.passed).toBe(false)
    expect((rg.checks as Array<Record<string, unknown>>)?.[0]?.ok).toBe(true)
  })
})
