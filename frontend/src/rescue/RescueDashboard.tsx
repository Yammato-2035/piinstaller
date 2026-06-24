import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { RESCUE_NAV_TILES, type RescueNavTileId } from './rescueNavTiles';
import { moveTileFocus } from './rescueKeyboardNav';
import { useRescueLayoutProfile } from './rescueLayout';
import { RESCUE_LOGO } from './rescueAssets';
import { RESCUE_TILE_COUNT } from './rescueTheme';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';
const tileIcon: Record<string, string> = {
  backup: '💾',
  rescue: '📁',
  migration: '🐼🧰',
  analyze: '🔍',
  network: '📶',
  partition: '🧩',
  install: '🐧',
  settings: '⚙️',
  system: '🖥️',
};

declare const __APP_VERSION__: string;

/** RS-P3M — centered dashboard with responsive tile grid. */
export const RescueDashboard: React.FC<{
  locale: RescueLocale;
  onSelectTile?: (id: RescueNavTileId) => void;
}> = ({ locale, onSelectTile }) => {
  const layout = useRescueLayoutProfile();
  const [focused, setFocused] = useState<RescueNavTileId>('backup_create');
  const dict = useMemo(() => getRescueDict(locale), [locale]);
  const version = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '';
  const tileRefs = useRef<Partial<Record<RescueNavTileId, HTMLButtonElement | null>>>({});

  const focusTile = useCallback((id: RescueNavTileId) => {
    setFocused(id);
    tileRefs.current[id]?.focus();
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(e.key)) {
        const next = moveTileFocus(focused, e.key, layout.tileCols);
        if (next) {
          e.preventDefault();
          focusTile(next);
        }
      }
      if (
        (e.key === 'Enter' || e.key === ' ') &&
        document.activeElement?.classList.contains('rescue-tile-btn')
      ) {
        e.preventDefault();
        onSelectTile?.(focused);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [focused, focusTile, onSelectTile, layout.tileCols]);

  return (
    <div className="rescue-dashboard" data-rescue-tile-count={RESCUE_TILE_COUNT}>
      <div className="rescue-brand-block rescue-brand-row">
        <img src={RESCUE_LOGO} alt="Setuphelfer" className="rescue-hero-logo" data-rescue-logo="true" />
        <div className="rescue-brand-text">
          <h1 className="rescue-brand-title" data-rescue-wordmark="true">
            <span>Setup</span>
            <span className="rescue-brand-green">helfer</span>
          </h1>
          <p className="rescue-brand-subtitle">{tPath(dict, 'subtitle')}</p>
          {version ? (
            <p className="rescue-brand-version" data-rescue-version="true">
              v{version}
            </p>
          ) : null}
        </div>
      </div>

      <section
        className="rescue-tile-grid"
        style={{ gridTemplateColumns: `repeat(${layout.tileCols}, minmax(0, 1fr))` }}
        aria-label={tPath(dict, 'menuPrompt')}
        data-rescue-tiles="true"
        data-rescue-tile-cols={layout.tileCols}
      >
        {RESCUE_NAV_TILES.map((tile) => {
          const active = focused === tile.id;
          return (
            <button
              key={tile.id}
              ref={(el) => {
                tileRefs.current[tile.id] = el;
              }}
              type="button"
              className={`rescue-tile-btn rescue-focus-ring${active ? ' rescue-tile-active' : ''}`}
              data-rescue-tile-id={tile.id}
              aria-label={tPath(dict, tile.titleKey)}
              onFocus={() => setFocused(tile.id)}
              onClick={() => {
                setFocused(tile.id);
                onSelectTile?.(tile.id);
              }}
            >
              <span className="rescue-tile-icon" aria-hidden>
                {tileIcon[tile.icon]}
              </span>
              <span className="rescue-tile-title">{tPath(dict, tile.titleKey)}</span>
              <span className="rescue-tile-subtitle">{tPath(dict, tile.subtitleKey)}</span>
            </button>
          );
        })}
      </section>

      <p className="rescue-hint">{tPath(dict, 'hint')}</p>
    </div>
  );
};
