/**
 * Phase 6: Risikostufen pro Modul/Seite.
 * GREEN = sichere Operationen, YELLOW = Systemänderungen, RED = gefährliche Operationen.
 */

import type { TFunction } from 'i18next'

export type RiskLevel = 'green' | 'yellow' | 'red'

export interface PageRiskInfo {
  level: RiskLevel
  label: string
  /** Kurzer Hinweis für die Warnkarte auf der Seite (nur bei yellow/red). */
  warningText?: string
}

type RiskEntry = { level: RiskLevel; warningKey?: string }

const RISK_MAP: Record<string, RiskEntry> = {
  dashboard: { level: 'green' },
  wizard: { level: 'green' },
  'app-store': { level: 'green' },
  backup: { level: 'green' },
  monitoring: { level: 'green' },
  documentation: { level: 'green' },
  settings: { level: 'green' },
  users: { level: 'green' },
  learning: { level: 'green' },
  'pi-installer-update': { level: 'green' },
  'dsi-radio-settings': { level: 'green' },

  security: {
    level: 'yellow',
    warningKey: 'risk.warning.security',
  },
  'control-center': {
    level: 'yellow',
    warningKey: 'risk.warning.controlCenter',
  },
  'periphery-scan': { level: 'yellow' },
  webserver: {
    level: 'yellow',
    warningKey: 'risk.warning.webserver',
  },
  nas: {
    level: 'yellow',
    warningKey: 'risk.warning.nas',
  },
  homeautomation: { level: 'yellow' },
  musicbox: { level: 'yellow' },
  'kino-streaming': { level: 'yellow' },
  presets: { level: 'yellow' },
  remote: { level: 'yellow' },
  devenv: {
    level: 'yellow',
    warningKey: 'risk.warning.devenv',
  },

  'raspberry-pi-config': {
    level: 'red',
    warningKey: 'risk.warning.raspberryPiConfig',
  },
  mailserver: {
    level: 'red',
    warningKey: 'risk.warning.mailserver',
  },
}

function labelKeyForLevel(level: RiskLevel): string {
  if (level === 'green') return 'risk.label.safe'
  if (level === 'yellow') return 'risk.label.systemChange'
  return 'risk.label.danger'
}

export function getPageRisk(pageId: string | undefined, t: TFunction): PageRiskInfo | null {
  if (!pageId) return null
  const raw = RISK_MAP[pageId]
  if (!raw) return null
  return {
    level: raw.level,
    label: t(labelKeyForLevel(raw.level)),
    warningText: raw.warningKey ? String(t(raw.warningKey)) : undefined,
  }
}

export function getRiskLevel(pageId: string | undefined): RiskLevel | null {
  const raw = pageId ? RISK_MAP[pageId] : null
  return raw?.level ?? null
}
