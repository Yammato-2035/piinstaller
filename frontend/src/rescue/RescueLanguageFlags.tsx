import React from 'react';

export const RescueLanguageFlags: React.FC<{
  locale: 'de' | 'en';
  onLocaleChange: (locale: 'de' | 'en') => void;
  labels: { de: string; en: string };
}> = ({ locale, onLocaleChange, labels }) => (
  <div role="group" aria-label={labels.de} className="rescue-language-flags" data-rescue-language="true">
    {(
      [
        { code: 'de' as const, flag: '🇩🇪', label: labels.de },
        { code: 'en' as const, flag: '🇬🇧', label: labels.en },
      ] as const
    ).map((item) => {
      const active = locale === item.code;
      return (
        <button
          key={item.code}
          type="button"
          className={`rescue-focus-ring rescue-top-icon-btn${active ? ' rescue-top-active' : ''}`}
          aria-pressed={active}
          aria-label={item.label}
          title={item.label}
          onClick={() => onLocaleChange(item.code)}
        >
          <span aria-hidden>{item.flag}</span>
        </button>
      );
    })}
  </div>
);
