/**
 * Professionelle Tool-Shell für den Partitionshelfer.
 */

import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, Shield, Lock } from 'lucide-react'
import { fetchApi } from '../api'
import { TOOL_SHELL } from '../lib/theme/setuphelferToolTheme'

interface Props {
  children: React.ReactNode
  onBack?: () => void
}

const PartitionToolShell: React.FC<Props> = ({ children, onBack }) => {
  const { t } = useTranslation()
  const [version, setVersion] = useState('—')

  useEffect(() => {
    void (async () => {
      try {
        const res = await fetchApi('/api/version')
        if (!res.ok) return
        const data = (await res.json()) as { project_version?: string }
        setVersion(String(data.project_version ?? '—'))
      } catch {
        /* ignore */
      }
    })()
  }, [])

  const goBack = () => {
    if (onBack) {
      onBack()
      return
    }
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href)
      url.searchParams.delete('page')
      url.searchParams.set('tab', 'backup')
      window.location.href = url.toString()
    }
  }

  return (
    <div className={TOOL_SHELL.page} data-testid="partition-tool-shell">
      <header className={`${TOOL_SHELL.chrome} px-4 sm:px-6 lg:px-8 py-4`}>
        <div className="flex flex-wrap items-center gap-4 justify-between max-w-[1920px] mx-auto">
          <div className="flex items-center gap-4 min-w-0">
            <img
              src="/assets/branding/logo/logo-main.svg"
              alt="Setuphelfer"
              className="h-10 w-10 shrink-0"
              data-testid="partition-tool-logo"
            />
            <div className="min-w-0">
              <h1 className={TOOL_SHELL.title}>{t('partitionTool.title')}</h1>
              <p className={TOOL_SHELL.subtitle}>{t('partitionTool.subtitle')}</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-red-500/40 bg-red-950/40 text-xs font-bold text-red-100"
              data-testid="partition-tool-readonly-badge"
            >
              <Lock className="w-3.5 h-3.5" />
              {t('partitionTool.readOnlyBadge')}
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-slate-600/50 bg-slate-800/60 text-xs font-semibold text-slate-300">
              <Shield className="w-3.5 h-3.5" />
              v{version}
            </span>
            <button
              type="button"
              onClick={goBack}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-slate-600/60 bg-slate-800 hover:bg-slate-700 text-sm font-semibold text-slate-100 transition-colors"
              data-testid="partition-tool-back"
            >
              <ArrowLeft className="w-4 h-4" />
              {t('partitionTool.backToSetuphelfer')}
            </button>
          </div>
        </div>
      </header>
      <main className={`${TOOL_SHELL.workspace} max-w-[1920px] mx-auto w-full`}>{children}</main>
    </div>
  )
}

export default PartitionToolShell
