import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { fetchApi } from '../../api'

type AIExportPanelProps = {
  statusQuery: string
}

export function AIExportPanel({ statusQuery }: AIExportPanelProps) {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [prompt, setPrompt] = useState('')

  const loadPrompt = async () => {
    setLoading(true)
    try {
      const r = await fetchApi(`/api/dev-dashboard/cursor-meta-prompt?${statusQuery}`)
      const d = await r.json().catch(() => ({}))
      if (d?.status === 'success' && typeof d.prompt === 'string') {
        setPrompt(d.prompt)
        await navigator.clipboard?.writeText(d.prompt).catch(() => undefined)
        toast.success(t('devDashboard.aiPrompt.copied'))
      } else {
        toast.error(t('devDashboard.noData'))
      }
    } catch {
      toast.error(t('devDashboard.noData'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-xl border border-indigo-600/50 bg-indigo-950/20 p-4" data-testid="dev-dashboard-ai-export-panel">
      <h2 className="text-base font-semibold text-white">{t('devDashboard.aiPrompt.title')}</h2>
      <p className="text-xs text-slate-300 mt-1">{t('devDashboard.aiPrompt.subtitle')}</p>
      <button
        type="button"
        className="btn-secondary mt-3 text-sm"
        disabled={loading}
        data-testid="dev-dashboard-ai-prompt-generate"
        onClick={() => void loadPrompt()}
      >
        {t('devDashboard.aiPrompt.generateButton')}
      </button>
      {prompt ? (
        <pre className="mt-3 max-h-48 overflow-auto text-xs bg-slate-950/80 p-3 rounded border border-slate-700 whitespace-pre-wrap">
          {prompt}
        </pre>
      ) : null}
    </div>
  )
}
