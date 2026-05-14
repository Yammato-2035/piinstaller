/** Pure filter helpers for Development Cockpit (unit-tested without jsdom). */

export type FilterKey = 'all' | 'red' | 'yellow' | 'green' | 'gray' | 'backup' | 'rescue' | 'diagnostics' | 'docs'

export type ModuleFilterRow = {
  status?: string
  area?: string
  docs?: string[]
  faq?: string[]
  knowledge_base?: string[]
}

export function toneClass(s: string): string {
  const x = String(s || '').toLowerCase()
  if (x === 'green') return 'border-emerald-600/50 bg-emerald-950/30 text-emerald-100'
  if (x === 'yellow') return 'border-amber-600/50 bg-amber-950/30 text-amber-100'
  if (x === 'red') return 'border-red-600/50 bg-red-950/30 text-red-100'
  return 'border-slate-600/50 bg-slate-900/40 text-slate-200'
}

export function matchesFilter(m: ModuleFilterRow, f: FilterKey): boolean {
  if (f === 'all') return true
  const st = String(m.status || '').toLowerCase()
  if (f === 'red' || f === 'yellow' || f === 'green' || f === 'gray') return st === f
  if (f === 'backup') return String(m.area || '').toLowerCase() === 'backup'
  if (f === 'rescue') return String(m.area || '').toLowerCase() === 'rescue'
  if (f === 'diagnostics') return String(m.area || '').toLowerCase() === 'diagnostics'
  if (f === 'docs') {
    const n = (m.docs?.length || 0) + (m.faq?.length || 0) + (m.knowledge_base?.length || 0)
    return n > 0
  }
  return true
}
