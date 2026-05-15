import React from 'react'
import { useTranslation } from 'react-i18next'
import type { DevDashboardCapabilities, DevDashboardDataSource } from '../../lib/devDashboard/types'

type StandaloneModeBannerProps = {
  source: DevDashboardDataSource
  apiReachable: boolean
  capabilities: DevDashboardCapabilities
  workspaceRoot?: string
}

export function StandaloneModeBanner({
  source,
  apiReachable,
  capabilities,
  workspaceRoot,
}: StandaloneModeBannerProps) {
  const { t } = useTranslation()
  if (apiReachable && source === 'runtime_api') return null

  return (
    <div
      className="rounded-lg border border-orange-600/60 bg-orange-950/40 px-4 py-4 text-sm text-orange-50 mb-4 space-y-3"
      data-testid="dev-dashboard-standalone-banner"
    >
      <p className="font-semibold text-orange-100">{t('devDashboard.standalone.bannerTitle')}</p>
      <p className="text-orange-100/90">{t('devDashboard.standalone.bannerBody')}</p>
      {workspaceRoot ? (
        <p className="text-xs font-mono text-orange-200/80">
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
      <p className="text-xs text-orange-200/70">
        {t('devDashboard.standalone.source')}: <code className="text-orange-100">{source}</code>
      </p>
    </div>
  )
}
