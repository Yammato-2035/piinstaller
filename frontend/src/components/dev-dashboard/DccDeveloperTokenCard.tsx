import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  readStoredDccDeveloperToken,
  verifyStoredDccDeveloperToken,
  writeStoredDccDeveloperToken,
  type DccTokenVerifyResult,
} from '../../lib/devDashboard/dccDeveloperToken'
import { fetchApi } from '../../api'

const HEADER_NAME = 'X-Setuphelfer-Developer-Token'

type Props = {
  onTokenChanged?: () => void
}

export function DccDeveloperTokenCard({ onTokenChanged }: Props) {
  const { t } = useTranslation()
  const [draft, setDraft] = useState('')
  const [stored, setStored] = useState(false)
  const [verifyState, setVerifyState] = useState<DccTokenVerifyResult | 'idle'>('idle')
  const [verifyMessage, setVerifyMessage] = useState<string | null>(null)

  const [serverConfigured, setServerConfigured] = useState<boolean | null>(null)

  const refreshStored = useCallback(() => {
    const token = readStoredDccDeveloperToken()
    setStored(Boolean(token))
    if (!token) setDraft('')
  }, [])

  useEffect(() => {
    refreshStored()
    const handler = () => refreshStored()
    window.addEventListener('setuphelfer-dcc-developer-token-changed', handler)
    void (async () => {
      try {
        const r = await fetchApi('/api/dev-dashboard/capability-status', { cache: 'no-store' })
        if (r.ok) {
          const body = (await r.json()) as { developer_capability_configured?: boolean }
          setServerConfigured(body.developer_capability_configured === true)
        }
      } catch {
        setServerConfigured(null)
      }
    })()
    return () => window.removeEventListener('setuphelfer-dcc-developer-token-changed', handler)
  }, [refreshStored])

  const save = () => {
    writeStoredDccDeveloperToken(draft.trim() || null)
    setDraft('')
    setStored(Boolean(draft.trim()))
    setVerifyState('idle')
    setVerifyMessage(null)
    onTokenChanged?.()
  }

  const verify = async () => {
    setVerifyState('idle')
    setVerifyMessage(null)
    const result = await verifyStoredDccDeveloperToken()
    setVerifyState(result)
    if (result === 'valid') setVerifyMessage(t('devDashboard.vis.token.verifyValid'))
    else if (result === 'invalid') setVerifyMessage(t('devDashboard.vis.token.verifyInvalid'))
    else if (result === 'missing') setVerifyMessage(t('devDashboard.vis.token.verifyMissing'))
    else setVerifyMessage(t('devDashboard.vis.token.verifyError'))
  }

  const clear = () => {
    writeStoredDccDeveloperToken(null)
    setDraft('')
    setStored(false)
    setVerifyState('idle')
    setVerifyMessage(null)
    onTokenChanged?.()
  }

  const statusKey =
    verifyState !== 'idle'
      ? `devDashboard.vis.token.status.${verifyState}`
      : stored
        ? 'devDashboard.vis.token.status.stored'
        : 'devDashboard.vis.token.status.missing'

  return (
    <section
      className="rounded-xl border border-violet-700/40 bg-violet-950/15 p-4 mb-4"
      data-testid="dcc-developer-token-card"
    >
      <h2 className="text-sm font-semibold text-white">{t('devDashboard.vis.token.title')}</h2>
      <p className="text-xs text-slate-400 mt-1">{t('devDashboard.vis.token.subtitle')}</p>

      <dl className="mt-3 grid gap-2 text-xs text-slate-300">
        <div>
          <dt className="text-slate-500">{t('devDashboard.vis.token.statusLabel')}</dt>
          <dd className="font-medium text-white" data-testid="dcc-token-status">
            {t(statusKey)}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.vis.token.headerLabel')}</dt>
          <dd className="font-mono text-violet-200">{HEADER_NAME}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.vis.token.sourceLabel')}</dt>
          <dd>{t('devDashboard.vis.token.sourceValue')}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.vis.token.serverConfigured')}</dt>
          <dd data-testid="dcc-token-server-configured">
            {serverConfigured === true
              ? t('devDashboard.vis.token.serverConfiguredYes')
              : serverConfigured === false
                ? t('devDashboard.vis.token.serverConfiguredNo')
                : '—'}
          </dd>
        </div>
      </dl>

      {serverConfigured && !stored ? (
        <p className="mt-2 text-xs text-amber-200/90 rounded border border-amber-700/40 bg-amber-950/20 px-2 py-1.5" data-testid="dcc-token-server-hint">
          {t('devDashboard.vis.token.serverHint')}
        </p>
      ) : null}

      <div className="mt-3 flex flex-wrap items-end gap-2">
        <label className="flex-1 min-w-[200px] text-xs text-slate-300">
          <span className="text-[10px] uppercase tracking-wide text-slate-500">
            {stored ? t('devDashboard.vis.token.replaceLabel') : t('devDashboard.vis.token.inputLabel')}
          </span>
          <input
            type="password"
            autoComplete="off"
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-xs text-white"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={stored ? t('devDashboard.vis.token.storedPlaceholder') : ''}
            data-testid="dcc-token-card-input"
          />
        </label>
        <button type="button" className="rounded bg-violet-700/80 px-3 py-1.5 text-xs text-white" onClick={save} data-testid="dcc-token-save">
          {t('devDashboard.vis.token.save')}
        </button>
        <button type="button" className="rounded border border-slate-600 px-3 py-1.5 text-xs text-slate-200" onClick={() => void verify()} data-testid="dcc-token-verify">
          {t('devDashboard.vis.token.verify')}
        </button>
        <button type="button" className="rounded border border-red-700/50 px-3 py-1.5 text-xs text-red-200" onClick={clear} data-testid="dcc-token-clear">
          {t('devDashboard.vis.token.clear')}
        </button>
      </div>

      {verifyMessage ? (
        <p
          className={`mt-2 text-xs ${verifyState === 'valid' ? 'text-emerald-300' : 'text-amber-200'}`}
          data-testid="dcc-token-verify-message"
        >
          {verifyMessage}
        </p>
      ) : null}
    </section>
  )
}
