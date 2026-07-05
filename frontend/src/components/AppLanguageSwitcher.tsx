import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import i18n, { APP_LOCALES, normalizeAppLocale, setAppLocale, type AppLocale } from '../i18n'

const LOCALE_META: Record<AppLocale, { short: string; labelKey: string; flag: string }> = {
  de: { short: 'DE', labelKey: 'settings.language.de', flag: '🇩🇪' },
  en: { short: 'EN', labelKey: 'settings.language.en', flag: '🇬🇧' },
  fr: { short: 'FR', labelKey: 'settings.language.fr', flag: '🇫🇷' },
  nl: { short: 'NL', labelKey: 'settings.language.nl', flag: '🇳🇱' },
}

type Variant = 'compact' | 'settings' | 'dcc'

type Props = {
  variant?: Variant
  showActiveLabel?: boolean
  className?: string
}

export function AppLanguageSwitcher({ variant = 'compact', showActiveLabel = false, className = '' }: Props) {
  const { t } = useTranslation()
  const [active, setActive] = useState<AppLocale>(() => normalizeAppLocale(i18n.language))

  useEffect(() => {
    const onChange = (lng: string) => setActive(normalizeAppLocale(lng))
    i18n.on('languageChanged', onChange)
    return () => {
      i18n.off('languageChanged', onChange)
    }
  }, [])

  const activeMeta = LOCALE_META[active]

  if (variant === 'settings') {
    return (
      <div className={className} data-testid="app-language-switcher-settings">
        {showActiveLabel ? (
          <p className="text-xs text-sky-300 mb-2" data-testid="app-language-active-label">
            {t('settings.language.active', { language: t(activeMeta.labelKey), code: activeMeta.short })}
          </p>
        ) : null}
        <div className="flex flex-wrap gap-2">
          {APP_LOCALES.map((lng) => {
            const meta = LOCALE_META[lng]
            const pressed = active === lng
            return (
              <button
                key={lng}
                type="button"
                onClick={() => setAppLocale(lng)}
                aria-pressed={pressed}
                data-testid={`app-language-${lng}`}
                className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                  pressed
                    ? 'bg-sky-600 text-white'
                    : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700 hover:text-white'
                }`}
              >
                {meta.flag} {t(meta.labelKey)}
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  const isDcc = variant === 'dcc'

  return (
    <div className={`flex flex-col items-end gap-1 ${className}`} data-testid="app-language-switcher">
      {showActiveLabel ? (
        <span className="text-[10px] text-slate-400" data-testid="app-language-active-label">
          {t('settings.language.activeShort', { code: activeMeta.short })}
        </span>
      ) : null}
      <div
        className={`inline-flex shrink-0 rounded-lg border overflow-hidden text-[11px] leading-none ${
          isDcc ? 'border-slate-600' : 'border-slate-300 dark:border-slate-600 shadow-sm'
        }`}
        role="group"
        aria-label={t('sidebar.language.aria')}
      >
        {APP_LOCALES.map((lng, idx) => {
          const meta = LOCALE_META[lng]
          const pressed = active === lng
          return (
            <button
              key={lng}
              type="button"
              onClick={() => setAppLocale(lng)}
              aria-pressed={pressed}
              title={t(meta.labelKey)}
              data-testid={`app-language-${lng}`}
              className={`px-2.5 py-1 flex items-center justify-center transition-colors ${
                idx > 0 ? 'border-l border-slate-300 dark:border-slate-600' : ''
              } ${
                pressed
                  ? 'bg-sky-600 text-white'
                  : isDcc
                    ? 'bg-slate-900 text-slate-200 hover:bg-slate-800'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {meta.short}
            </button>
          )
        })}
      </div>
    </div>
  )
}
