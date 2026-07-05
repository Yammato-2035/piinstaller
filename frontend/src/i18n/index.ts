import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import de from '../locales/de.json'
import en from '../locales/en.json'
import fr from '../locales/fr.json'
import nl from '../locales/nl.json'
import dccVisDe from '../locales/dccVis001.de.json'
import dccVisEn from '../locales/dccVis001.en.json'
import dccVisFr from '../locales/dccVis001.fr.json'
import dccVisNl from '../locales/dccVis001.nl.json'

const deMerged = { ...de, ...dccVisDe }
const enMerged = { ...en, ...dccVisEn }
const frMerged = { ...fr, ...dccVisFr }
const nlMerged = { ...nl, ...dccVisNl }

export const LOCALE_STORAGE_KEY = 'setuphelfer-ui-locale'
export const APP_LOCALES = ['de', 'en', 'fr', 'nl'] as const
export type AppLocale = (typeof APP_LOCALES)[number]

export function normalizeAppLocale(lng: string | undefined | null): AppLocale {
  const code = String(lng || 'de').toLowerCase().slice(0, 2)
  if (code === 'en' || code === 'fr' || code === 'nl') return code
  return 'de'
}

function detectInitialLng(): AppLocale {
  try {
    const saved = localStorage.getItem(LOCALE_STORAGE_KEY)
    if (saved) return normalizeAppLocale(saved)
  } catch {
    /* ignore */
  }
  const nav = typeof navigator !== 'undefined' ? navigator.language?.toLowerCase() ?? '' : ''
  if (nav.startsWith('de')) return 'de'
  if (nav.startsWith('en')) return 'en'
  if (nav.startsWith('fr')) return 'fr'
  if (nav.startsWith('nl')) return 'nl'
  return 'de'
}

void i18n.use(initReactI18next).init({
  resources: {
    de: { translation: deMerged },
    en: { translation: enMerged },
    fr: { translation: frMerged },
    nl: { translation: nlMerged },
  },
  lng: typeof window !== 'undefined' ? detectInitialLng() : 'de',
  fallbackLng: 'de',
  supportedLngs: [...APP_LOCALES],
  interpolation: { escapeValue: false },
  /** Keys wie `platform.appTitle.setuphelfer` sind einzelne Strings, keine Verschachtelung. */
  keySeparator: false,
})

export function setAppLocale(lng: AppLocale) {
  void i18n.changeLanguage(lng)
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, lng)
    window.dispatchEvent(new CustomEvent('setuphelfer-ui-locale-changed', { detail: { lng } }))
  } catch {
    /* ignore */
  }
}

export default i18n
