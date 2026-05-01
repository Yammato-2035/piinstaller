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

export const TAURI_DEFAULT_API = 'http://127.0.0.1:8000';
const DEFAULT_API_TIMEOUT_MS = 12000;

/** LocalStorage-Key für optionale Backend-URL (z. B. wenn Backend auf anderem Rechner läuft). */
export const API_BASE_STORAGE_KEY = 'pi-installer-api-base';

/** Erfahrungslevel nur im Browser, wenn die Profil-API nicht erreichbar ist (z. B. kein Backend, kein Vite-Proxy). */
export const EXPERIENCE_LEVEL_LOCAL_KEY = 'setuphelfer-experience-level-v1';

export type StoredExperienceLevel = 'beginner' | 'advanced' | 'developer';

export function readStoredExperienceLevel(): StoredExperienceLevel | null {
  try {
    const v = typeof localStorage !== 'undefined' ? localStorage.getItem(EXPERIENCE_LEVEL_LOCAL_KEY) : null;
    const l = String(v || '').toLowerCase();
    if (l === 'beginner' || l === 'advanced' || l === 'developer') return l;
  } catch {
    /* ignore */
  }
  return null;
}

function writeStoredExperienceLevel(level: StoredExperienceLevel): void {
  try {
    localStorage.setItem(EXPERIENCE_LEVEL_LOCAL_KEY, level);
  } catch {
    /* ignore */
  }
}

/** Liest Erfahrungslevel vom Backend; bei Fehlschlag null (Caller kann readStoredExperienceLevel nutzen). */
export async function fetchExperienceLevelFromApi(): Promise<StoredExperienceLevel | null> {
  try {
    const res = await fetchApi('/api/user-profile');
    if (res.ok) {
      const data = (await res.json()) as { profile?: { experience_level?: string } };
      const raw = data?.profile?.experience_level;
      if (raw) {
        const l = String(raw).toLowerCase();
        if (l === 'beginner' || l === 'advanced' || l === 'developer') return l;
      }
    }
  } catch {
    /* ignore */
  }
  try {
    const res = await fetchApi('/api/settings');
    if (res.ok) {
      const data = (await res.json()) as { experience_level?: string };
      const raw = data?.experience_level;
      if (raw) {
        const l = String(raw).toLowerCase();
        if (l === 'beginner' || l === 'advanced' || l === 'developer') return l;
      }
    }
  } catch {
    /* ignore */
  }
  return null;
}

/**
 * Basis-URL nur bis zum Host (Port), ohne trailing slash.
 * Entfernt ein fälschlich angehängtes `/api` – sonst würde fetchApi(`/api/...`) nach `/api/api/...` auflösen (404).
 */
export function normalizeApiBaseUrl(raw: string): string {
  let v = raw.trim().replace(/\/+$/, '')
  if (v.toLowerCase().endsWith('/api')) {
    v = v.slice(0, -4).replace(/\/+$/, '')
  }
  return v
}

function isValidApiBaseUrl(raw: string): boolean {
  try {
    const u = new URL(raw)
    if (u.protocol !== 'http:' && u.protocol !== 'https:') return false
    // Expliziter Port muss im gültigen TCP-Bereich liegen.
    if (u.port) {
      const p = Number(u.port)
      if (!Number.isInteger(p) || p < 1 || p > 65535) return false
    }
    return true
  } catch {
    return false
  }
}

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

/** API-Basis-URL (leer = gleiche Origin, für Proxy). Gespeicherte URL hat Vorrang vor Build-Zeit-VITE_API_BASE. */
export function getApiBase(): string {
  try {
    const stored = typeof localStorage !== 'undefined' ? localStorage.getItem(API_BASE_STORAGE_KEY) : null;
    if (stored && typeof stored === 'string' && stored.trim()) {
      const normalized = normalizeApiBaseUrl(stored)
      if (isValidApiBaseUrl(normalized)) return normalized
      // Defekten Eintrag bereinigen, damit Tauri auf den sicheren Default zurückfällt.
      localStorage.removeItem(API_BASE_STORAGE_KEY)
    }
  } catch {
    // ignore
  }
  const env = import.meta.env.VITE_API_BASE as string | undefined;
  if (env && typeof env === 'string') return normalizeApiBaseUrl(env);
  // Tauri Dev: Seite von Vite (localhost:5173) – relative /api nutzen, Vite-Proxy leitet weiter.
  if (typeof window !== 'undefined' && window.__TAURI__ && import.meta.env.DEV) return '';
  if (typeof window !== 'undefined' && window.__TAURI__) return TAURI_DEFAULT_API;
  return '';
}

/** Setzt die Backend-URL (z. B. nach erfolgreichem Fallback-Test) und löst API-Base-Change aus. */
export function setApiBase(url: string): void {
  try {
    const v = normalizeApiBaseUrl(url);
    if (v) localStorage.setItem(API_BASE_STORAGE_KEY, v);
    else localStorage.removeItem(API_BASE_STORAGE_KEY);
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('pi-installer-api-base-changed'));
    }
  } catch {
    // ignore
  }
}

export async function fetchApi(path: string, init?: RequestInit): Promise<Response> {
  const base = getApiBase();
  const url = base ? `${base}${path.startsWith('/') ? '' : '/'}${path}` : path;
  const headers = new Headers(init?.headers);
  if (_screenshotMode) headers.set('X-Demo-Mode', '1');
  if (init?.signal) {
    return fetch(url, { ...init, headers });
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_API_TIMEOUT_MS);
  try {
    return await fetch(url, { ...init, headers, signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
}

/** Profil speichern: mehrere API-Pfade, sonst localStorage (kein Pi / kein Backend / 404 vom statischen Server). */
export async function saveUserProfilePayload(body: Record<string, unknown>): Promise<Response> {
  const initBase: RequestInit = {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
  const tryReq = async (path: string, method: string): Promise<Response> => {
    try {
      return await fetchApi(path, { method, ...initBase })
    } catch {
      return new Response(null, { status: 0, statusText: 'NetworkError' })
    }
  }

  let r = await tryReq('/api/user-profile', 'PUT')
  if (r.ok) {
    const lv = typeof body.experience_level === 'string' ? body.experience_level.toLowerCase() : ''
    if (lv === 'beginner' || lv === 'advanced' || lv === 'developer') writeStoredExperienceLevel(lv)
    return r
  }
  if (r.status === 404 || r.status === 405) {
    r = await tryReq('/api/user-profile', 'POST')
    if (r.ok) {
      const lv = typeof body.experience_level === 'string' ? body.experience_level.toLowerCase() : ''
      if (lv === 'beginner' || lv === 'advanced' || lv === 'developer') writeStoredExperienceLevel(lv)
      return r
    }
  }
  if (r.status === 404 || r.status === 405) {
    r = await tryReq('/api/settings/user-experience', 'POST')
    if (r.ok) {
      const lv = typeof body.experience_level === 'string' ? body.experience_level.toLowerCase() : ''
      if (lv === 'beginner' || lv === 'advanced' || lv === 'developer') writeStoredExperienceLevel(lv)
      return r
    }
  }

  const level = typeof body.experience_level === 'string' ? body.experience_level.toLowerCase() : ''
  const offlineOk =
    (level === 'beginner' || level === 'advanced' || level === 'developer') &&
    (r.status === 404 ||
      r.status === 405 ||
      r.status === 0 ||
      r.status === 502 ||
      r.status === 503)
  if (offlineOk) {
    writeStoredExperienceLevel(level)
    return new Response(
      JSON.stringify({
        status: 'success',
        profile: { experience_level: level, updated_at: new Date().toISOString() },
        _savedLocally: true,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    )
  }
  return r
}
