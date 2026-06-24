/** RS-P3L — minimal design tokens (no layout tricks). */
export const rescueTheme = {
  bg: '#000000',
  bgPanel: '#111111',
  bgElevated: '#1a1a1a',
  cardFrom: '#1d4ed8',
  cardTo: '#2563eb',
  text: '#ffffff',
  textMuted: '#cbd5e1',
  textDim: '#94a3b8',
  accent: '#96c93d',
  brandGreen: '#96c93d',
  statusOk: '#22c55e',
  statusWarn: '#eab308',
  statusErr: '#ef4444',
  focus: '#fbbf24',
  border: 'rgba(148, 163, 184, 0.4)',
  shellWidth: 1400,
  fontSizePageTitle: 42,
  font: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
  fontSizeBase: 18,
  fontSizeMin: 16,
  fontSizeButton: 22,
} as const;

export const RESCUE_TILE_COUNT = 9;
