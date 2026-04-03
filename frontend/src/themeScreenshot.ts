/**
 * Marketing-/Theme-Screenshots: per URL ?themeShot=… (nur DEV oder VITE_THEME_SCREENSHOTS=1).
 * Wird von scripts/capture-theme-screenshots.mjs angesteuert.
 */
export type ThemeShot = 'start' | 'experience' | 'webserver' | 'error' | 'dashboard'

export function getThemeShot(): ThemeShot | null {
  if (typeof window === 'undefined') return null
  const allow =
    Boolean(import.meta.env.DEV) || String(import.meta.env.VITE_THEME_SCREENSHOTS || '') === 'true'
  if (!allow) return null
  const s = new URLSearchParams(window.location.search).get('themeShot')
  if (s === 'start' || s === 'experience' || s === 'webserver' || s === 'error' || s === 'dashboard') {
    return s
  }
  return null
}

export function isThemeScreenshotCapture(): boolean {
  return getThemeShot() !== null
}
