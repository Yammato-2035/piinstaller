import React from 'react';
import { RESCUE_LOGO } from './rescueAssets';
import { rescueTheme as t } from './rescueTheme';

export const RescueBrandingHeader: React.FC<{
  subtitle?: string;
  title?: string;
  version?: string;
  variant?: 'hero' | 'compact';
}> = ({ subtitle, title, version, variant = 'hero' }) => {
  if (variant !== 'hero') {
    return (
      <header className="rescue-brand-block rescue-page-header">
        <h2 className="rescue-page-title">{title}</h2>
        {subtitle ? <p className="rescue-page-subtitle">{subtitle}</p> : null}
      </header>
    );
  }

  return (
    <header className="rescue-brand-block">
      <img src={RESCUE_LOGO} alt="Setuphelfer" className="rescue-hero-logo" />
      <h1 className="rescue-brand-title">
        <span>Setup</span>
        <span className="rescue-brand-green">helfer</span>
      </h1>
      {subtitle ? <p className="rescue-brand-subtitle">{subtitle}</p> : null}
      {version ? <p className="rescue-brand-version">v{version}</p> : null}
    </header>
  );
};
