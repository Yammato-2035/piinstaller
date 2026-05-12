import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import de from '../locales/de.json'
import en from '../locales/en.json'

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
    de: { translation: de },
    en: { translation: en },
  },
  lng: typeof window !== 'undefined' ? detectInitialLng() : 'de',
  fallbackLng: 'de',
  supportedLngs: ['de', 'en'],
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
