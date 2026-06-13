/**
 * Professionelles Tool-Design für Setuphelfer-Werkzeugmodus (Partitionshelfer).
 */

import { toolStatusToneFromRisk, type ToolStatusTone } from '../../viewmodels/statusViewModel'

export type { ToolStatusTone }

export const TOOL_STATUS: Record<
  ToolStatusTone,
  { panel: string; text: string; badge: string; border: string }
> = {
  safe: {
    panel: 'bg-emerald-950/40 border-emerald-600/35',
    text: 'text-emerald-100',
    badge: 'bg-emerald-600/25 text-emerald-50 border-emerald-500/45',
    border: 'border-emerald-500/40',
  },
  review: {
    panel: 'bg-amber-950/40 border-amber-600/35',
    text: 'text-amber-100',
    badge: 'bg-amber-600/25 text-amber-50 border-amber-500/45',
    border: 'border-amber-500/40',
  },
  blocked: {
    panel: 'bg-red-950/45 border-red-600/40',
    text: 'text-red-100',
    badge: 'bg-red-600/30 text-red-50 border-red-500/50',
    border: 'border-red-500/45',
  },
  info: {
    panel: 'bg-sky-950/35 border-sky-600/30',
    text: 'text-sky-100',
    badge: 'bg-sky-600/25 text-sky-50 border-sky-500/40',
    border: 'border-sky-500/35',
  },
  unknown: {
    panel: 'bg-slate-900/55 border-slate-600/40',
    text: 'text-slate-300',
    badge: 'bg-slate-700/40 text-slate-200 border-slate-500/40',
    border: 'border-slate-600/45',
  },
}

export const TOOL_SHELL = {
  page: 'min-h-0 flex flex-col bg-slate-950 text-slate-100',
  chrome: 'border-b border-slate-700/60 bg-slate-900/90 backdrop-blur-sm',
  workspace: 'flex-1 min-h-0 p-4 sm:p-6 lg:p-8',
  panel: 'rounded-lg border border-slate-700/50 bg-slate-900/70 shadow-sm',
  panelHeader: 'text-sm font-bold uppercase tracking-[0.12em] text-slate-300',
  title: 'text-xl sm:text-2xl font-black text-slate-50 tracking-tight',
  subtitle: 'text-sm text-slate-400',
  mono: 'font-mono text-xs text-slate-500',
}

export const TOOL_DISK_ROLE: Record<string, ToolStatusTone> = {
  linux_system_disk: 'blocked',
  windows_system_disk: 'blocked',
  mixed_system_disk: 'blocked',
  rescue_stick: 'info',
  backup_target: 'safe',
  backup_source: 'blocked',
  external_data_disk: 'review',
  internal_data_disk: 'unknown',
  unknown_disk: 'review',
  system: 'blocked',
  backup: 'safe',
  rescue: 'info',
  other: 'unknown',
}

export function riskToTone(risk: string | undefined): ToolStatusTone {
  return toolStatusToneFromRisk(risk)
}
