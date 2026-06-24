import React from 'react';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';
import { RescueBrandingHeader } from './RescueBrandingHeader';
import { rescueTheme as theme } from './rescueTheme';

export const RescueSectionPage: React.FC<{
  titleKey: string;
  subtitleKey?: string;
  locale: RescueLocale;
  onBack: () => void;
  embedded?: boolean;
  children: React.ReactNode;
}> = ({ titleKey, subtitleKey, locale, onBack, embedded = true, children }) => {
  const dict = getRescueDict(locale);
  const title = tPath(dict, titleKey);
  const subtitle = subtitleKey ? tPath(dict, subtitleKey) : '';

  return (
    <div
      style={{
        width: '100%',
        color: theme.text,
        fontSize: 18,
        ...(embedded
          ? {}
          : {
              minHeight: '100vh',
              background: theme.bg,
              fontFamily: theme.font,
              padding: '20px 16px 32px',
            }),
      }}
    >
      <button type="button" className="rescue-focus-ring rescue-back-btn" onClick={onBack}>
        ← {tPath(dict, 'common.back')}
      </button>

      <RescueBrandingHeader variant="compact" title={title} subtitle={subtitle} />

      <div className="rescue-section-panel">{children}</div>
    </div>
  );
};
