/**
 * Workbench-Shell – eigenständiges Werkzeug-Feeling (read-only).
 */

import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, Lock } from 'lucide-react'
import { fetchApi } from '../../api'
import { TOOL_SHELL } from '../../lib/theme/setuphelferToolTheme'

interface Props {
  children: React.ReactNode
  onBack?: () => void
}

const PartitionWorkbenchShell: React.FC<Props> = ({ children, onBack }) => {
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
    <div className={TOOL_SHELL.page} data-testid="partition-workbench-shell">
      <header className={`${TOOL_SHELL.chrome} border-slate-800`}>
        <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4 min-w-0">
              <img
                src="/assets/branding/logo/logo-main.svg"
                alt="Setuphelfer"
                className="h-11 w-11 shrink-0"
                data-testid="partition-workbench-logo"
              />
              <div className="min-w-0 border-l border-slate-700/60 pl-4">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">
                  Setuphelfer
                </p>
                <h1
                  className="text-lg sm:text-xl font-black text-slate-50 uppercase tracking-wide"
                  data-testid="partition-workbench-title"
                >
                  {t('partitionWorkbench.title')}
                </h1>
                <ul className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-slate-400">
                  <li>{t('partitionWorkbench.tagline.detect')}</li>
                  <li>{t('partitionWorkbench.tagline.risks')}</li>
                  <li>{t('partitionWorkbench.tagline.restore')}</li>
                </ul>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={goBack}
                className="inline-flex items-center gap-2 px-4 py-2 rounded border border-slate-600/70 bg-slate-800/80 hover:bg-slate-700 text-sm font-semibold text-slate-100 transition-colors"
                data-testid="partition-workbench-back"
              >
                <ArrowLeft className="w-4 h-4" />
                {t('partitionTool.backToSetuphelfer')}
              </button>
              <span
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-red-500/45 bg-red-950/50 text-xs font-bold text-red-100 uppercase tracking-wide"
                data-testid="partition-workbench-readonly"
              >
                <Lock className="w-3.5 h-3.5" />
                {t('partitionTool.readOnlyBadge')}
              </span>
              <span
                className="inline-flex items-center px-3 py-1.5 rounded border border-slate-600/50 bg-slate-900/70 text-xs font-mono font-semibold text-slate-300"
                data-testid="partition-workbench-version"
              >
                v{version}
              </span>
            </div>
          </div>
        </div>
      </header>
      <main className={`${TOOL_SHELL.workspace} max-w-[1920px] mx-auto w-full flex-1 min-h-0`}>
        {children}
      </main>
    </div>
  )
}

export default PartitionWorkbenchShell
