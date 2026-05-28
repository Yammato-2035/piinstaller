import React from 'react'
import { useTranslation } from 'react-i18next'
import type { DevDashboardCapabilities, DevDashboardDataSource } from '../../lib/devDashboard/types'

type StandaloneModeBannerProps = {
  source: DevDashboardDataSource
  apiReachable: boolean
  capabilities: DevDashboardCapabilities
  workspaceRoot?: string
  offlineReason?: string
}

export function StandaloneModeBanner({
  source,
  apiReachable,
  capabilities,
  workspaceRoot,
  offlineReason,
}: StandaloneModeBannerProps) {
  const { t } = useTranslation()
  if (apiReachable && source === 'runtime_api') return null
  const isBackendHang = String(offlineReason || '').includes('backend_hanging_timeout')
  const borderClass = isBackendHang ? 'border-red-600/60 bg-red-950/40 text-red-50' : 'border-orange-600/60 bg-orange-950/40 text-orange-50'
  const titleClass = isBackendHang ? 'text-red-100' : 'text-orange-100'
  const bodyClass = isBackendHang ? 'text-red-100/90' : 'text-orange-100/90'
  const mutedClass = isBackendHang ? 'text-red-200/80' : 'text-orange-200/80'
  const footerClass = isBackendHang ? 'text-red-200/70' : 'text-orange-200/70'
  const codeClass = isBackendHang ? 'text-red-100' : 'text-orange-100'
  const reasonText = isBackendHang
    ? t('devDashboard.standalone.backendHangReason')
    : t('devDashboard.standalone.backendOfflineReason')

  return (
    <div
      className={`rounded-lg border px-4 py-4 text-sm mb-4 space-y-3 ${borderClass}`}
      data-testid="dev-dashboard-standalone-banner"
    >
      <p className={`font-semibold ${titleClass}`}>
        {isBackendHang ? t('devDashboard.standalone.backendHangTitle') : t('devDashboard.standalone.bannerTitle')}
      </p>
      <p className={bodyClass}>{t('devDashboard.standalone.bannerBody')}</p>
      <p className="text-xs">
        {t('devDashboard.standalone.detectedState')}: <strong>{reasonText}</strong>
      </p>
      <p className="text-xs">{t('devDashboard.standalone.nextOperatorStep')}</p>
      {workspaceRoot ? (
        <p className={`text-xs font-mono ${mutedClass}`}>
          {t('devDashboard.standalone.workspaceRoot')}: {workspaceRoot}
        </p>
      ) : null}
      <ul className="grid sm:grid-cols-2 gap-1 text-xs" data-testid="dev-dashboard-standalone-capabilities">
        <li>
          {t('devDashboard.standalone.cap.runtimeGate')}:{' '}
          <strong>{t('devDashboard.standalone.blocked')}</strong>
        </li>
        <li>
          {t('devDashboard.standalone.cap.api')}:{' '}
          <strong>{apiReachable ? t('devDashboard.standalone.online') : t('devDashboard.standalone.offline')}</strong>
        </li>
        <li>
          {t('devDashboard.standalone.cap.workspace')}:{' '}
          <strong>
            {capabilities.workspaceAnalysis
              ? t('devDashboard.standalone.available')
              : t('devDashboard.standalone.unavailable')}
          </strong>
        </li>
        <li>
          {t('devDashboard.standalone.cap.structure')}:{' '}
          <strong>
            {capabilities.structureHealth
              ? t('devDashboard.standalone.available')
              : t('devDashboard.standalone.unavailable')}
          </strong>
        </li>
        <li>
          {t('devDashboard.standalone.cap.roadmap')}:{' '}
          <strong>
            {capabilities.roadmap ? t('devDashboard.standalone.available') : t('devDashboard.standalone.unavailable')}
          </strong>
        </li>
        <li>
          {t('devDashboard.standalone.cap.prompt')}:{' '}
          <strong>
            {capabilities.promptExport
              ? t('devDashboard.standalone.available')
              : t('devDashboard.standalone.unavailable')}
          </strong>
        </li>
        <li className="sm:col-span-2">
          {t('devDashboard.standalone.cap.runtimeTests')}:{' '}
          <strong>{t('devDashboard.standalone.locked')}</strong>
        </li>
      </ul>
      <p className={`text-xs ${footerClass}`}>
        {t('devDashboard.standalone.source')}: <code className={codeClass}>{source}</code>
      </p>
    </div>
  )
}
