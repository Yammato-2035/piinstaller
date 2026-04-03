/**
 * URLs zu Dateien unter `public/assets/mascot/…`.
 * - Nutzt Vite `import.meta.env.BASE_URL` (unter Tauri i. d. R. `./`).
 * - Löst im Browser mit `URL` gegen die aktuelle Seite auf, damit img-Src in Tauri/WebView zuverlässig funktioniert.
 */
export function mascotPublicUrl(relativePath: string): string {
  const trimmed = relativePath.replace(/^\/+/, '')
  const base = import.meta.env.BASE_URL ?? '/'

  if (typeof window !== 'undefined' && window.location?.href) {
    try {
      const baseResolved = new URL(base, window.location.origin)
      return new URL(trimmed, baseResolved).href
    } catch {
      // Fallback unten
    }
  }

  const prefix = base.endsWith('/') ? base : `${base}/`
  return `${prefix}${trimmed}`
}
