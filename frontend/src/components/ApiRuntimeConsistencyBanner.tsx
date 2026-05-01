import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { TAURI_DEFAULT_API, getApiBase, normalizeApiBaseUrl, setApiBase } from '../api'

const EXPECTED_TAURI_APP_ID = 'de.pi-installer.app'

function frontendBuildVersion(): string {
  return typeof __APP_VERSION__ !== 'undefined' ? String(__APP_VERSION__).trim() : '0.0.0'
}

type BannerState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'ok'; backendVersion: string; apiBaseLabel: string }
  | { kind: 'unreachable'; apiBaseLabel: string }
  | { kind: 'version_mismatch'; backendVersion: string; uiVersion: string; apiBaseLabel: string }
  | { kind: 'app_id_mismatch'; got: string; apiBaseLabel: string }

export default function ApiRuntimeConsistencyBanner() {
  const { t } = useTranslation()
  const [state, setState] = useState<BannerState>({ kind: 'idle' })

  const runCheck = useCallback(async () => {
    if (typeof window === 'undefined') return
    setState({ kind: 'loading' })
    const base = getApiBase()
    const apiBaseLabel = base ? normalizeApiBaseUrl(base) : t('app.apiConsistency.apiBase.sameOrigin')
    const path = '/api/version'
    const url = base ? `${base.replace(/\/+$/, '')}${path}` : path
    const uiVer = frontendBuildVersion()
    try {
      const ctrl = new AbortController()
      const tid = window.setTimeout(() => ctrl.abort(), 12_000)
      const res = await fetch(url, { signal: ctrl.signal, credentials: 'omit' })
      window.clearTimeout(tid)
      if (!res.ok) {
        setState({ kind: 'unreachable', apiBaseLabel })
        return
      }
      const data = (await res.json()) as {
        version?: string
        tauri_app_id?: string
        app_name?: string
      }
      const backendVersion = String(data?.version || '').trim()
      if (!backendVersion) {
        setState({ kind: 'unreachable', apiBaseLabel })
        return
      }
      const tidExpect = data.tauri_app_id
      if (tidExpect && tidExpect !== EXPECTED_TAURI_APP_ID) {
        setState({ kind: 'app_id_mismatch', got: tidExpect, apiBaseLabel })
        return
      }
      if (backendVersion !== uiVer) {
        setState({
          kind: 'version_mismatch',
          backendVersion,
          uiVersion: uiVer,
          apiBaseLabel,
        })
        return
      }
      setState({ kind: 'ok', backendVersion, apiBaseLabel })
    } catch {
      setState({ kind: 'unreachable', apiBaseLabel })
    }
  }, [t])

  useEffect(() => {
    void runCheck()
  }, [runCheck])

  useEffect(() => {
    const onBaseChange = () => void runCheck()
    window.addEventListener('pi-installer-api-base-changed', onBaseChange)
    return () => window.removeEventListener('pi-installer-api-base-changed', onBaseChange)
  }, [runCheck])

  const resetToDefault = () => {
    const isTauri = !!(window as unknown as { __TAURI__?: unknown }).__TAURI__
    if (isTauri) {
      setApiBase(TAURI_DEFAULT_API)
    } else {
      setApiBase('')
    }
    void runCheck()
  }

  if (state.kind === 'idle' || state.kind === 'loading') return null
  if (state.kind === 'ok') return null

  if (state.kind === 'unreachable') {
    return (
      <div
        className="flex-none border-b border-amber-400/80 bg-amber-100 px-4 py-2 text-sm text-amber-950 dark:border-amber-600 dark:bg-amber-950/40 dark:text-amber-100"
        role="alert"
      >
        <p className="font-medium">{t('app.apiConsistency.unreachableTitle')}</p>
        <p className="mt-1 opacity-90">
          {t('app.apiConsistency.apiBaseLabel')}: <code className="rounded bg-black/10 px-1">{state.apiBaseLabel}</code>
        </p>
        <p className="mt-1 text-xs opacity-90">{t('app.apiConsistency.unreachableHint')}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-md bg-amber-800 px-3 py-1 text-xs font-medium text-white hover:bg-amber-900 dark:bg-amber-600 dark:hover:bg-amber-500"
            onClick={resetToDefault}
          >
            {t('app.apiConsistency.resetApiBase')}
          </button>
          <button
            type="button"
            className="rounded-md border border-amber-800/40 px-3 py-1 text-xs hover:bg-amber-200/50 dark:border-amber-400/40 dark:hover:bg-amber-900/30"
            onClick={() => void runCheck()}
          >
            {t('app.apiConsistency.retry')}
          </button>
        </div>
      </div>
    )
  }

  if (state.kind === 'version_mismatch') {
    return (
      <div
        className="flex-none border-b border-amber-500/80 bg-amber-50 px-4 py-2 text-sm text-amber-950 dark:border-amber-500 dark:bg-amber-950/30 dark:text-amber-50"
        role="status"
      >
        <p className="font-medium">{t('app.apiConsistency.versionMismatchTitle')}</p>
        <p className="mt-1 text-xs">
          {t('app.apiConsistency.uiBuild')}: <code className="rounded bg-black/10 px-1">{state.uiVersion}</code> —{' '}
          {t('app.apiConsistency.backend')}: <code className="rounded bg-black/10 px-1">{state.backendVersion}</code>
        </p>
        <p className="mt-1 text-xs opacity-90">
          {t('app.apiConsistency.apiBaseLabel')}: <code className="rounded bg-black/10 px-1">{state.apiBaseLabel}</code>
        </p>
        <p className="mt-1 text-xs">{t('app.apiConsistency.versionMismatchHint')}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-md bg-amber-800 px-3 py-1 text-xs font-medium text-white hover:bg-amber-900 dark:bg-amber-600"
            onClick={resetToDefault}
          >
            {t('app.apiConsistency.resetApiBase')}
          </button>
        </div>
      </div>
    )
  }

  if (state.kind === 'app_id_mismatch') {
    return (
      <div
        className="flex-none border-b border-rose-400 bg-rose-50 px-4 py-2 text-sm text-rose-950 dark:border-rose-700 dark:bg-rose-950/40 dark:text-rose-100"
        role="alert"
      >
        <p className="font-medium">{t('app.apiConsistency.appIdMismatchTitle')}</p>
        <p className="mt-1 text-xs">
          {t('app.apiConsistency.expectedId')}: <code className="rounded bg-black/10 px-1">{EXPECTED_TAURI_APP_ID}</code> —{' '}
          {t('app.apiConsistency.received')}: <code className="rounded bg-black/10 px-1">{state.got}</code>
        </p>
        <p className="mt-1 text-xs opacity-90">{t('app.apiConsistency.appIdMismatchHint')}</p>
      </div>
    )
  }

  return null
}
