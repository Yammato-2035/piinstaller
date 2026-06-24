import React from 'react';
import { getRescueDict, languageLabel, RESCUE_LOCALES, type RescueLocale } from './rescueLocale';

export const RescueLanguageSelect: React.FC<{
  locale: RescueLocale;
  onLocaleChange: (locale: RescueLocale) => void;
}> = ({ locale, onLocaleChange }) => {
  const dict = getRescueDict(locale);

  return (
    <label className="rescue-language-select-wrap">
      <span className="visually-hidden">{languageLabel(dict, locale)}</span>
      <select
        className="rescue-focus-ring rescue-language-select"
        value={locale}
        aria-label={languageLabel(dict, locale)}
        onChange={(e) => onLocaleChange(e.target.value as RescueLocale)}
      >
        {RESCUE_LOCALES.map((item) => (
          <option key={item.code} value={item.code}>
            {item.flag} {languageLabel(dict, item.code)}
          </option>
        ))}
      </select>
    </label>
  );
};
