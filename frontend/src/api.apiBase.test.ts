import { beforeEach, describe, expect, it, vi } from 'vitest'

const storage = new Map<string, string>()

vi.stubGlobal('localStorage', {
  getItem: (k: string) => storage.get(k) ?? null,
  setItem: (k: string, v: string) => {
    storage.set(k, v)
  },
  removeItem: (k: string) => {
    storage.delete(k)
  },
})

describe('api base (production vs dev)', () => {
  beforeEach(() => {
    storage.clear()
    vi.resetModules()
    vi.unstubAllEnvs()
    vi.stubGlobal('window', { __TAURI__: undefined } as Window & typeof globalThis)
  })

  async function loadApi() {
    return import('./api')
  }

  it('production web defaults to http://127.0.0.1:8000', async () => {
    vi.stubEnv('DEV', false)
    vi.stubEnv('PROD', true)
    const { getApiBase, getDefaultApiBase, usesViteDevProxy } = await loadApi()
    expect(usesViteDevProxy()).toBe(false)
    expect(getDefaultApiBase()).toBe('http://127.0.0.1:8000')
    expect(getApiBase()).toBe('http://127.0.0.1:8000')
  })

  it('vite dev web uses empty base for proxy', async () => {
    vi.stubEnv('DEV', true)
    vi.stubEnv('PROD', false)
    const { getApiBase, getDefaultApiBase, usesViteDevProxy } = await loadApi()
    expect(usesViteDevProxy()).toBe(true)
    expect(getDefaultApiBase()).toBe('')
    expect(getApiBase()).toBe('')
  })

  it('resetApiBaseToDefault sets production URL in release mode', async () => {
    vi.stubEnv('DEV', false)
    vi.stubEnv('PROD', true)
    const { resetApiBaseToDefault, getApiBase, API_BASE_STORAGE_KEY } = await loadApi()
    storage.set(API_BASE_STORAGE_KEY, 'http://192.168.1.99:8000')
    resetApiBaseToDefault()
    expect(getApiBase()).toBe('http://127.0.0.1:8000')
    expect(storage.get(API_BASE_STORAGE_KEY)).toBe('http://127.0.0.1:8000')
  })

  it('stored URL overrides default in production', async () => {
    vi.stubEnv('DEV', false)
    vi.stubEnv('PROD', true)
    const { getApiBase, API_BASE_STORAGE_KEY } = await loadApi()
    storage.set(API_BASE_STORAGE_KEY, 'http://192.168.1.10:8000')
    expect(getApiBase()).toBe('http://192.168.1.10:8000')
  })
})
