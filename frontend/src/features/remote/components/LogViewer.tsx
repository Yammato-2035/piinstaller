import React from 'react'

interface Widget {
  id: string
  type: string
  label?: string
}

interface LogViewerProps {
  widget: Widget
  state: Record<string, unknown>
}

export default function LogViewer({ widget, state }: LogViewerProps) {
  const label = widget.label || widget.id
  const logs = (state.last_logs as string[]) || []
  return (
    <div className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4">
      <h3 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">{label}</h3>
      <div className="max-h-40 overflow-y-auto font-mono text-xs text-slate-700 dark:text-slate-200 bg-slate-200 dark:bg-slate-900 rounded-lg p-2">
        {logs.length === 0 ? (
          <p className="text-slate-500">Keine Logs</p>
        ) : (
          logs.map((line, i) => (
            <div key={i} className="whitespace-pre-wrap break-all">
              {line}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
