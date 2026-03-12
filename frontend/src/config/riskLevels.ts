/**
 * Phase 6: Risikostufen pro Modul/Seite.
 * GREEN = sichere Operationen, YELLOW = Systemänderungen, RED = gefährliche Operationen.
 */

export type RiskLevel = 'green' | 'yellow' | 'red'

export interface PageRiskInfo {
  level: RiskLevel
  label: string
  /** Kurzer Hinweis für die Warnkarte auf der Seite (nur bei yellow/red). */
  warningText?: string
}

const RISK_MAP: Record<string, PageRiskInfo> = {
  dashboard: { level: 'green', label: 'Sicher' },
  wizard: { level: 'green', label: 'Sicher' },
  'app-store': { level: 'green', label: 'Sicher' },
  backup: { level: 'green', label: 'Sicher' },
  monitoring: { level: 'green', label: 'Sicher' },
  documentation: { level: 'green', label: 'Sicher' },
  settings: { level: 'green', label: 'Sicher' },
  users: { level: 'green', label: 'Sicher' },
  learning: { level: 'green', label: 'Sicher' },
  'pi-installer-update': { level: 'green', label: 'Sicher' },
  'dsi-radio-settings': { level: 'green', label: 'Sicher' },

  security: {
    level: 'yellow',
    label: 'Systemänderung',
    warningText: 'Firewall, SSH und automatische Updates verändern die Systemkonfiguration. Änderungen sind in der Regel rückgängig zu machen.',
  },
  'control-center': {
    level: 'yellow',
    label: 'Systemänderung',
    warningText: 'Hier werden Netzwerk-, Display- und Geräteeinstellungen geändert. Bitte nur anpassen, wenn du die Auswirkungen kennst.',
  },
  'periphery-scan': { level: 'yellow', label: 'Systemänderung' },
  webserver: {
    level: 'yellow',
    label: 'Systemänderung',
    warningText: 'Installation und Konfiguration von Webservern (Nginx/Apache) verändern Dienste und Ports.',
  },
  nas: {
    level: 'yellow',
    label: 'Systemänderung',
    warningText: 'NAS-Einrichtung kann Speicher und Dienste auf dem System anpassen.',
  },
  homeautomation: { level: 'yellow', label: 'Systemänderung' },
  musicbox: { level: 'yellow', label: 'Systemänderung' },
  'kino-streaming': { level: 'yellow', label: 'Systemänderung' },
  presets: { level: 'yellow', label: 'Systemänderung' },
  remote: { level: 'yellow', label: 'Systemänderung' },
  devenv: {
    level: 'yellow',
    label: 'Systemänderung',
    warningText: 'Entwicklungsumgebung installiert zusätzliche Software und kann Systempfade betreffen.',
  },

  'raspberry-pi-config': {
    level: 'red',
    label: 'Gefahr',
    warningText: 'Änderungen an der Raspberry-Pi-Konfiguration (config.txt, Overclocking, Boot-Optionen) können das System beschädigen oder unbootbar machen. Nur mit Erfahrung nutzen.',
  },
  mailserver: {
    level: 'red',
    label: 'Gefahr',
    warningText: 'Ein Mailserver im Internet erfordert DNS, SPF, DKIM und sichere Konfiguration. Fehler können zu offenen Relays oder Blocklisten führen. Nur für erfahrene Nutzer.',
  },
}

export function getPageRisk(pageId: string | undefined): PageRiskInfo | null {
  if (!pageId) return null
  return RISK_MAP[pageId] ?? null
}

export function getRiskLevel(pageId: string | undefined): RiskLevel | null {
  const info = getPageRisk(pageId)
  return info?.level ?? null
}
