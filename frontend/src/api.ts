/**
 * Zentrale API-Basis-URL und fetch-Wrapper.
 * Im Browser: relative /api (Proxy oder Same-Origin).
 * In Tauri-Desktop-App: absolute URL (z. B. http://localhost:8000), da kein Same-Origin.
 */

declare global {
  interface Window {
    __TAURI__?: unknown;
  }
}

const TAURI_DEFAULT_API = 'http://localhost:8000';

export function getApiBase(): string {
  const env = import.meta.env.VITE_API_BASE as string | undefined;
  if (env && typeof env === 'string') return env.replace(/\/$/, '');
  if (typeof window !== 'undefined' && window.__TAURI__) return TAURI_DEFAULT_API;
  return '';
}

export async function fetchApi(path: string, init?: RequestInit): Promise<Response> {
  const base = getApiBase();
  const url = base ? `${base}${path.startsWith('/') ? '' : '/'}${path}` : path;
  return fetch(url, init);
}
