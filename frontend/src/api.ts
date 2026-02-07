/**
 * Zentrale API-Basis-URL und fetch-Wrapper.
 * Im Browser: relative /api (Proxy oder Same-Origin).
 * In Tauri-Desktop-App: absolute URL (z. B. http://127.0.0.1:8000), da kein Same-Origin.
 * 127.0.0.1 statt localhost für zuverlässige IPv4-Verbindung (localhost kann zu IPv6 ::1 auflösen).
 * Screenshot-Modus: X-Demo-Mode Header für Platzhalterdaten (keine IPs/Benutzernamen).
 */

declare global {
  interface Window {
    __TAURI__?: unknown;
  }
}

const TAURI_DEFAULT_API = 'http://127.0.0.1:8000';

/** Wenn true, werden API-Anfragen mit X-Demo-Mode: 1 gesendet (Platzhalter für Screenshots). */
let _screenshotMode = false;

export function setScreenshotMode(enabled: boolean): void {
  _screenshotMode = enabled;
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('pi-installer-screenshot-mode-changed', { detail: { enabled } }));
  }
}

export function isScreenshotMode(): boolean {
  return _screenshotMode;
}

export function getApiBase(): string {
  const env = import.meta.env.VITE_API_BASE as string | undefined;
  if (env && typeof env === 'string') return env.replace(/\/$/, '');
  // Tauri Dev: Seite von Vite (localhost:5173) – relative /api nutzen, Vite-Proxy leitet weiter.
  // Verhindert CORS-Probleme im WebKit-WebView auf Pi/Wayland.
  if (typeof window !== 'undefined' && window.__TAURI__ && import.meta.env.DEV) return '';
  if (typeof window !== 'undefined' && window.__TAURI__) return TAURI_DEFAULT_API;
  return '';
}

export async function fetchApi(path: string, init?: RequestInit): Promise<Response> {
  const base = getApiBase();
  const url = base ? `${base}${path.startsWith('/') ? '' : '/'}${path}` : path;
  const headers = new Headers(init?.headers);
  if (_screenshotMode) headers.set('X-Demo-Mode', '1');
  return fetch(url, { ...init, headers });
}
