/**
 * Entwicklungs-Dashboard-Strip am Partitionsmanager (Phase 2.3 Mockup).
 */

import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { LayoutDashboard } from 'lucide-react'
import { fetchApi } from '../api'
import { MOCKUP_SECTION, MOCKUP_STATUS } from '../lib/partition/partitionMockupTheme'

interface Props {
  safetyChecksOk: boolean
  onOpenDashboard?: () => void
}

const PartitionPageDevStrip: React.FC<Props> = ({ safetyChecksOk, onOpenDashboard }) => {
  const { t } = useTranslation()
  const [backendOk, setBackendOk] = useState<boolean | null>(null)
  const [version, setVersion] = useState<string>('—')
  const [profile, setProfile] = useState<string>('—')

  const probe = useCallback(async () => {
    try {
      const res = await fetchApi('/api/version')
      if (!res.ok) {
        setBackendOk(false)
        return
      }
      const data = (await res.json()) as {
        project_version?: string
        version?: string
        runtime_profile?: string
        profile?: string
      }
      setVersion(String(data.project_version ?? data.version ?? '—'))
      setProfile(String(data.runtime_profile ?? data.profile ?? '—'))
      setBackendOk(true)
    } catch {
      setBackendOk(false)
    }
  }, [])

  useEffect(() => {
    void probe()
  }, [probe])

  const openDashboard = () => {
    if (onOpenDashboard) {
      onOpenDashboard()
      return
    }
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href)
      url.searchParams.set('page', 'dev-dashboard')
      window.location.href = url.toString()
    }
  }

  const pills: Array<{ key: string; label: string; tone: keyof typeof MOCKUP_STATUS }> = [
    {
      key: 'backend',
      label: backendOk ? t('partitionManager.devStrip.backendOk') : t('partitionManager.devStrip.backendFail'),
      tone: backendOk ? 'safe' : 'blocked',
    },
    {
      key: 'safety',
      label: t('partitionManager.devStrip.safetyActive'),
      tone: safetyChecksOk ? 'safe' : 'review',
    },
    {
      key: 'version',
      label: t('partitionManager.devStrip.version', { version }),
      tone: 'info',
    },
    {
      key: 'profile',
      label: t('partitionManager.devStrip.profile', { profile }),
      tone: 'info',
    },
  ]

  return (
    <div className={`${MOCKUP_SECTION} border-violet-500/25`} data-testid="partition-dev-strip">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <p className="text-sm font-black uppercase tracking-[0.14em] text-violet-200">
          {t('partitionManager.devStrip.title')}
        </p>
        <button
          type="button"
          onClick={openDashboard}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-violet-500/40 text-violet-100 text-sm font-bold hover:bg-violet-950/50 transition-colors"
        >
          <LayoutDashboard className="w-4 h-4" />
          {t('partitionManager.devStrip.openDashboard')}
        </button>
      </div>
      <div className="flex flex-wrap gap-2 mt-4">
        {pills.map(({ key, label, tone }) => (
          <span
            key={key}
            className={`inline-flex items-center px-3 py-1.5 rounded-full border text-xs font-bold ${MOCKUP_STATUS[tone].pill}`}
            data-testid={`partition-dev-pill-${key}`}
          >
            {label}
          </span>
        ))}
      </div>
    </div>
  )
}

export default PartitionPageDevStrip
