/**
 * ActionQueueBar.tsx – Queue-Leiste + Bestätigungsdialog.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { CheckCircle, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchQueue, removeFromQueue, clearQueue, applyQueue, type PlannedAction } from '../../api/partitionApi'

interface ActionQueueBarProps {
  onApplied: () => void
}

const ActionQueueBar: React.FC<ActionQueueBarProps> = ({ onApplied }) => {
  const { t } = useTranslation()
  const [actions, setActions] = useState<PlannedAction[]>([])
  const [confirmOpen, setConfirmOpen] = useState(false)

  const reload = useCallback(async () => {
    try {
      setActions(await fetchQueue())
    } catch {
      setActions([])
    }
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  if (actions.length === 0) return null
  const hasBlocked = actions.some((a) => !a.execution_allowed)

  return (
    <>
      <div className="border-t border-slate-700/50 bg-slate-800/80 backdrop-blur">
        <div className="px-4 py-2 space-y-1">
          {actions.map((a) => (
            <div
              key={a.id}
              className={`flex items-center gap-2 text-xs rounded px-2 py-1 ${
                a.execution_allowed ? 'bg-slate-700/30' : 'bg-red-500/10 border border-red-500/20'
              }`}
            >
              <span className={a.execution_allowed ? 'text-emerald-400' : 'text-red-400'}>
                {a.execution_allowed ? '✓' : '✗'}
              </span>
              <span className="text-slate-300 flex-1 truncate">{a.beschreibung}</span>
              <button
                type="button"
                onClick={async () => {
                  await removeFromQueue(a.id)
                  reload()
                }}
                className="text-slate-500 hover:text-red-400 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
        <div className="flex items-center justify-between px-4 py-2 border-t border-slate-700/30">
          <span className="text-xs text-slate-400">
            {hasBlocked ? t('partition.queue.hasBlocked') : t('partition.queue.count', { count: actions.length })}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={async () => {
                await clearQueue()
                reload()
              }}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-700/60 hover:bg-slate-700 text-slate-400 transition-colors"
            >
              {t('partition.queue.clear')}
            </button>
            <button
              type="button"
              disabled={hasBlocked}
              onClick={() => setConfirmOpen(true)}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 disabled:opacity-40 disabled:cursor-not-allowed text-slate-900 font-semibold transition-colors"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              {t('partition.queue.apply')}
            </button>
          </div>
        </div>
      </div>
      {confirmOpen && (
        <ConfirmDialog
          actions={actions}
          onConfirm={async () => {
            setConfirmOpen(false)
            try {
              const result = await applyQueue(true)
              toast.success(result.message ?? t('partition.queue.apply'))
              onApplied()
            } catch {
              toast.error(t('partition.scan.error'))
            }
            reload()
          }}
          onCancel={() => setConfirmOpen(false)}
        />
      )}
    </>
  )
}

const ConfirmDialog: React.FC<{
  actions: PlannedAction[]
  onConfirm: () => void
  onCancel: () => void
}> = ({ actions, onConfirm, onCancel }) => {
  const [typed, setTyped] = useState('')
  const confirmed = typed.trim().toUpperCase() === 'ANWENDEN'
  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={(e) => e.target === e.currentTarget && onCancel()}
    >
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-md mx-4 overflow-hidden">
        <div className="bg-amber-900/40 border-b border-amber-700/30 px-5 py-3">
          <p className="text-amber-200 text-sm font-semibold text-center">
            ⚠️ Diese Aktionen können nicht rückgängig gemacht werden
          </p>
        </div>
        <div className="p-5 space-y-4">
          <div className="space-y-1.5">
            {actions.map((a) => (
              <div key={a.id} className="flex items-start gap-2 text-xs">
                <span className="text-emerald-400 mt-0.5">●</span>
                <span className="text-slate-300">{a.beschreibung}</span>
              </div>
            ))}
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-2">
              Tippe <span className="font-mono font-bold text-white">ANWENDEN</span> um fortzufahren:
            </p>
            <input
              autoFocus
              value={typed}
              onChange={(e) => setTyped(e.target.value)}
              className="w-full bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
              placeholder="ANWENDEN"
            />
          </div>
          <div className="flex justify-between pt-1">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 rounded-lg bg-slate-700/60 text-slate-400 text-sm hover:bg-slate-700 transition-colors"
            >
              Abbrechen
            </button>
            <button
              type="button"
              disabled={!confirmed}
              onClick={onConfirm}
              className="px-4 py-2 rounded-lg bg-red-500 hover:bg-red-400 disabled:opacity-30 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors"
            >
              ✓ Jetzt ausführen
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ActionQueueBar
