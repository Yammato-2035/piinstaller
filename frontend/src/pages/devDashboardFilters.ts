/** Pure filter helpers for Development Cockpit (unit-tested without jsdom). */

import {
  dashboardToneBorderClass,
  dashboardToneFromInput,
  isDashboardTrafficFilterKey,
} from '../viewmodels/statusViewModel'

export type FilterKey = 'all' | 'red' | 'yellow' | 'green' | 'gray' | 'backup' | 'rescue' | 'diagnostics' | 'docs'

export type ModuleFilterRow = {
  status?: string
  area?: string
  docs?: string[]
  faq?: string[]
  knowledge_base?: string[]
}

export function toneClass(s: string): string {
  return dashboardToneBorderClass(dashboardToneFromInput(s))
}

export function matchesFilter(m: ModuleFilterRow, f: FilterKey): boolean {
  if (f === 'all') return true
  const st = String(m.status || '').toLowerCase()
  if (isDashboardTrafficFilterKey(f)) return st === f
  if (f === 'backup') return String(m.area || '').toLowerCase() === 'backup'
  if (f === 'rescue') return String(m.area || '').toLowerCase() === 'rescue'
  if (f === 'diagnostics') return String(m.area || '').toLowerCase() === 'diagnostics'
  if (f === 'docs') {
    const n = (m.docs?.length || 0) + (m.faq?.length || 0) + (m.knowledge_base?.length || 0)
    return n > 0
  }
  return true
}
