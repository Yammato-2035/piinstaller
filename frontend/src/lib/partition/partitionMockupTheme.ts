/**
 * Zentrales Farb- und Layout-Konzept Partitionsmanager (Mockup Phase 2.3).
 * Setuphelfer: grün=sicher, gelb=prüfen, rot=blockiert, blau=information.
 */

import type { DiskRole } from './partitionRoleUtils'

export type MockupStatusTone = 'safe' | 'review' | 'blocked' | 'info'

export const MOCKUP_STATUS: Record<
  MockupStatusTone,
  { badge: string; card: string; text: string; pill: string }
> = {
  safe: {
    badge: 'bg-emerald-500/30 border-emerald-400/55 text-emerald-50',
    card: 'bg-emerald-950/35 border-emerald-500/40',
    text: 'text-emerald-200',
    pill: 'bg-emerald-500/25 text-emerald-100 border-emerald-500/45',
  },
  review: {
    badge: 'bg-amber-500/30 border-amber-400/55 text-amber-50',
    card: 'bg-amber-950/35 border-amber-500/40',
    text: 'text-amber-200',
    pill: 'bg-amber-500/25 text-amber-100 border-amber-500/45',
  },
  blocked: {
    badge: 'bg-red-500/30 border-red-400/55 text-red-50',
    card: 'bg-red-950/40 border-red-500/45',
    text: 'text-red-200',
    pill: 'bg-red-500/25 text-red-100 border-red-500/45',
  },
  info: {
    badge: 'bg-sky-500/30 border-sky-400/55 text-sky-50',
    card: 'bg-sky-950/35 border-sky-500/40',
    text: 'text-sky-200',
    pill: 'bg-sky-500/25 text-sky-100 border-sky-500/45',
  },
}

export const MOCKUP_DISK_ROLE: Record<
  DiskRole,
  {
    shell: string
    selected: string
    iconWrap: string
    icon: string
    label: string
  }
> = {
  system: {
    shell: 'border-orange-500/35 bg-orange-950/20',
    selected: 'border-orange-400/80 bg-orange-950/35 shadow-lg shadow-orange-900/30 ring-2 ring-orange-400/40',
    iconWrap: 'bg-orange-500/20',
    icon: 'text-orange-300',
    label: 'text-orange-300/90',
  },
  backup: {
    shell: 'border-emerald-500/35 bg-emerald-950/20',
    selected: 'border-emerald-400/80 bg-emerald-950/35 shadow-lg shadow-emerald-900/30 ring-2 ring-emerald-400/40',
    iconWrap: 'bg-emerald-500/20',
    icon: 'text-emerald-300',
    label: 'text-emerald-300/90',
  },
  rescue: {
    shell: 'border-sky-500/35 bg-sky-950/20',
    selected: 'border-sky-400/80 bg-sky-950/35 shadow-lg shadow-sky-900/30 ring-2 ring-sky-400/40',
    iconWrap: 'bg-sky-500/20',
    icon: 'text-sky-300',
    label: 'text-sky-300/90',
  },
  other: {
    shell: 'border-slate-600/50 bg-slate-800/40',
    selected: 'border-slate-400/70 bg-slate-800/60 shadow-lg shadow-slate-900/40 ring-2 ring-slate-400/30',
    iconWrap: 'bg-slate-700/60',
    icon: 'text-slate-400',
    label: 'text-slate-400',
  },
}

export const MOCKUP_SECTION = 'rounded-2xl border border-slate-700/45 bg-slate-900/45 p-5 sm:p-6 shadow-sm'

export const MOCKUP_RISK_BADGE: Record<string, string> = {
  green: `${MOCKUP_STATUS.safe.badge} border`,
  yellow: `${MOCKUP_STATUS.review.badge} border`,
  red: `${MOCKUP_STATUS.blocked.badge} border`,
}

export function statusLevelToTone(level: 'ok' | 'warning' | 'blocked'): MockupStatusTone {
  if (level === 'ok') return 'safe'
  if (level === 'warning') return 'review'
  return 'blocked'
}
