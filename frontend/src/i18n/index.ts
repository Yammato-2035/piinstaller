import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import de from '../locales/de.json'
import en from '../locales/en.json'
import dccVisDe from '../locales/dccVis001.de.json'
import dccVisEn from '../locales/dccVis001.en.json'
import dccVisFr from '../locales/dccVis001.fr.json'
import dccVisNl from '../locales/dccVis001.nl.json'

const deMerged = { ...de, ...dccVisDe }
const enMerged = { ...en, ...dccVisEn }
const frMerged = { ...enMerged, ...dccVisFr }
const nlMerged = { ...enMerged, ...dccVisNl }

export const LOCALE_STORAGE_KEY = 'setuphelfer-ui-locale'

function detectInitialLng(): string {
  try {
    const saved = localStorage.getItem(LOCALE_STORAGE_KEY)
    if (saved === 'en' || saved === 'de') return saved
  } catch {
    /* ignore */
  }
  const nav = typeof navigator !== 'undefined' ? navigator.language?.toLowerCase() ?? '' : ''
  if (nav.startsWith('de')) return 'de'
  if (nav.startsWith('en')) return 'en'
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
  supportedLngs: ['de', 'en', 'fr', 'nl'],
  interpolation: { escapeValue: false },
  /** Keys wie `platform.appTitle.setuphelfer` sind einzelne Strings, keine Verschachtelung. */
  keySeparator: false,
})

export function setAppLocale(lng: 'de' | 'en') {
  void i18n.changeLanguage(lng)
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, lng)
  } catch {
    /* ignore */
  }
}

export default i18n
