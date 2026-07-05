import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

const { i18nMock } = vi.hoisted(() => ({
  i18nMock: {
    language: 'de',
    on: vi.fn(),
    off: vi.fn(),
  },
}))
i18nMock.on.mockReturnValue(i18nMock)
i18nMock.off.mockReturnValue(i18nMock)

vi.mock('../i18n', () => ({
  default: i18nMock,
  APP_LOCALES: ['de', 'en', 'fr', 'nl'],
  normalizeAppLocale: (lng: string) =>
    lng?.slice(0, 2) === 'en' ? 'en' : lng?.slice(0, 2) === 'fr' ? 'fr' : lng?.slice(0, 2) === 'nl' ? 'nl' : 'de',
  setAppLocale: vi.fn(),
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, string>) => {
      if (key === 'settings.language.activeShort') return `Lang:${opts?.code ?? ''}`
      if (key.startsWith('settings.language.')) return key
      return key
    },
    i18n: i18nMock,
  }),
}))

import { AppLanguageSwitcher } from './AppLanguageSwitcher'

describe('AppLanguageSwitcher', () => {
  it('renders four locale buttons in compact mode', () => {
    const html = renderToStaticMarkup(React.createElement(AppLanguageSwitcher, { variant: 'compact', showActiveLabel: true }))
    expect(html).toContain('data-testid="app-language-de"')
    expect(html).toContain('data-testid="app-language-en"')
    expect(html).toContain('data-testid="app-language-fr"')
    expect(html).toContain('data-testid="app-language-nl"')
    expect(html).toContain('app-language-active-label')
  })
})
