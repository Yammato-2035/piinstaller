import { describe, expect, it } from 'vitest'
import { matchesFilter, toneClass } from './devDashboardFilters'

describe('devDashboardFilters', () => {
  const mod = {
    status: 'yellow',
    area: 'backup',
    docs: ['docs/x.md'],
    faq: [],
    knowledge_base: [],
  }

  it('matches traffic filters', () => {
    expect(matchesFilter(mod, 'all')).toBe(true)
    expect(matchesFilter(mod, 'yellow')).toBe(true)
    expect(matchesFilter(mod, 'red')).toBe(false)
    expect(matchesFilter(mod, 'green')).toBe(false)
  })

  it('matches area filters', () => {
    expect(matchesFilter(mod, 'backup')).toBe(true)
    expect(matchesFilter(mod, 'rescue')).toBe(false)
    expect(matchesFilter({ area: 'rescue' }, 'rescue')).toBe(true)
  })

  it('docs filter counts doc paths', () => {
    expect(matchesFilter({ docs: [], faq: [], knowledge_base: [] }, 'docs')).toBe(false)
    expect(matchesFilter({ faq: ['a.md'] }, 'docs')).toBe(true)
  })

  it('toneClass maps known statuses', () => {
    expect(toneClass('red')).toContain('red')
    expect(toneClass('unknown')).toContain('slate')
  })
})
