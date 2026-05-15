/** Erkennt externes Cockpit-Fenster (Tauri label oder URL-Parameter). */
export const COCKPIT_WINDOW_LABEL = 'cockpit'
export const COCKPIT_URL_PARAM = 'window'
export const COCKPIT_URL_VALUE = 'cockpit'

export function isCockpitWindow(): boolean {
  if (typeof window === 'undefined') return false
  const params = new URLSearchParams(window.location.search)
  if (params.get(COCKPIT_URL_PARAM) === COCKPIT_URL_VALUE) return true
  if (import.meta.env.VITE_COCKPIT_ONLY === 'true') return true
  return false
}

export function cockpitUrl(base?: string): string {
  const b = base || (typeof window !== 'undefined' ? window.location.origin + window.location.pathname : '/')
  const u = new URL(b, typeof window !== 'undefined' ? window.location.href : 'http://localhost/')
  u.searchParams.set(COCKPIT_URL_PARAM, COCKPIT_URL_VALUE)
  return u.toString()
}

export const COCKPIT_REFRESH_KEY = 'setuphelfer-cockpit-refresh-sec-v1'
export const DEFAULT_COCKPIT_REFRESH_SEC = 10

export function readCockpitRefreshSec(): number {
  try {
    const raw = localStorage.getItem(COCKPIT_REFRESH_KEY)
    const n = Number(raw)
    if (Number.isFinite(n) && n >= 5 && n <= 15) return Math.round(n)
  } catch {
    /* ignore */
  }
  return DEFAULT_COCKPIT_REFRESH_SEC
}

export function writeCockpitRefreshSec(sec: number): void {
  const clamped = Math.min(15, Math.max(5, Math.round(sec)))
  try {
    localStorage.setItem(COCKPIT_REFRESH_KEY, String(clamped))
  } catch {
    /* ignore */
  }
}
