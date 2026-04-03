/**
 * Zentrales Modell für Einsteiger-Führung und Bereichslogik (Frontend).
 */

export type ExperienceLevel = 'beginner' | 'advanced' | 'developer'

export type ModuleId =
  | 'dashboard'
  | 'wizard'
  | 'app-store'
  | 'backup'
  | 'monitoring'
  | 'documentation'
  | 'settings'
  | 'remote'
  | 'presets'
  | 'security'
  | 'users'
  | 'control-center'
  | 'periphery-scan'
  | 'webserver'
  | 'nas'
  | 'homeautomation'
  | 'musicbox'
  | 'kino-streaming'
  | 'learning'
  | 'devenv'
  | 'mailserver'
  | 'raspberry-pi-config'
  | 'pi-installer-update'
  | 'dsi-radio-settings'
  | 'tft'

/** Panda-/Begleiter-Art für Modulkontext (UI). */
export type CompanionVariant =
  | 'start'
  | 'tutorial'
  | 'backup'
  | 'cloud'
  | 'security'
  | 'base'
  | 'install'
  | 'debug'

/** Semantische Ampel für Modul / System-Hinweis (nicht identisch mit LampTriState-Strings überall). */
export type TrafficLightState = 'green' | 'yellow' | 'red' | 'unknown'

/** Ob und wie ein Bereich für Einsteiger erreichbar ist. */
export type AvailabilityState = 'available' | 'locked' | 'coming_later' | 'advanced_only'

export interface BeginnerModuleDefinition {
  id: ModuleId
  title: string
  subtitle: string
  companionVariant: CompanionVariant
  /** Im Einsteiger-Sidebar sichtbar */
  beginnerVisible: boolean
  /** Empfohlene erste Aktion (Label + optionale Zielseite) */
  beginnerPrimaryAction?: { label: string; targetPage?: ModuleId }
  availability: AvailabilityState
  trafficLightState: TrafficLightState
  lockedForBeginner: boolean
  comingLater: boolean
  warningKey?: string
  warningText?: string
  /** Optional: Badge in Einsteiger-Navigation (z. B. „optional fortgeschritten“). */
  beginnerNavBadge?: 'locked' | 'later' | 'advanced'
}

export const MODULE_DEFINITIONS: Record<ModuleId, BeginnerModuleDefinition> = {
  dashboard: {
    id: 'dashboard',
    title: 'Übersicht',
    subtitle: 'Status, nächster Schritt und Kurzaktionen.',
    companionVariant: 'start',
    beginnerVisible: true,
    beginnerPrimaryAction: { label: 'Übersicht prüfen' },
    availability: 'available',
    trafficLightState: 'unknown',
    lockedForBeginner: false,
    comingLater: false,
    warningText: 'Gelbe oder rote Ampeln: Hinweis ernst nehmen und dem empfohlenen Schritt folgen.',
  },
  wizard: {
    id: 'wizard',
    title: 'Installation',
    subtitle: 'Geführtes Setup – empfohlen als Erstes.',
    companionVariant: 'install',
    beginnerVisible: true,
    beginnerPrimaryAction: { label: 'Installation starten', targetPage: 'wizard' },
    availability: 'available',
    trafficLightState: 'green',
    lockedForBeginner: false,
    comingLater: false,
  },
  'app-store': {
    id: 'app-store',
    title: 'Apps',
    subtitle: 'Zusatzsoftware installieren.',
    companionVariant: 'tutorial',
    beginnerVisible: true,
    beginnerPrimaryAction: { label: 'Apps ansehen', targetPage: 'app-store' },
    availability: 'available',
    trafficLightState: 'unknown',
    lockedForBeginner: false,
    comingLater: false,
    warningText: 'Ein-Klick-Installation wird schrittweise erweitert.',
  },
  backup: {
    id: 'backup',
    title: 'Backup',
    subtitle: 'Sichern und Wiederherstellen.',
    companionVariant: 'backup',
    beginnerVisible: true,
    beginnerPrimaryAction: { label: 'Backup öffnen', targetPage: 'backup' },
    availability: 'available',
    trafficLightState: 'yellow',
    lockedForBeginner: false,
    comingLater: false,
    warningText: 'Vor Wiederherstellung: Warnhinweise lesen – Daten können überschrieben werden.',
  },
  monitoring: {
    id: 'monitoring',
    title: 'Monitoring',
    subtitle: 'Systemlast und Dienste beobachten.',
    companionVariant: 'debug',
    beginnerVisible: true,
    beginnerPrimaryAction: { label: 'Monitoring öffnen', targetPage: 'monitoring' },
    availability: 'available',
    trafficLightState: 'unknown',
    lockedForBeginner: false,
    comingLater: false,
    warningText: 'Viele Kennzahlen – für den Einstieg optional.',
    beginnerNavBadge: 'advanced',
  },
  documentation: {
    id: 'documentation',
    title: 'Dokumentation',
    subtitle: 'Anleitungen und Hilfe.',
    companionVariant: 'tutorial',
    beginnerVisible: true,
    availability: 'available',
    trafficLightState: 'unknown',
    lockedForBeginner: false,
    comingLater: false,
  },
  settings: {
    id: 'settings',
    title: 'Einstellungen',
    subtitle: 'App und Erfahrungslevel.',
    companionVariant: 'base',
    beginnerVisible: true,
    beginnerPrimaryAction: { label: 'Einstellungen', targetPage: 'settings' },
    availability: 'available',
    trafficLightState: 'unknown',
    lockedForBeginner: false,
    comingLater: false,
  },
  remote: {
    id: 'remote',
    title: 'Remote',
    subtitle: 'Fernzugriff.',
    companionVariant: 'base',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  presets: {
    id: 'presets',
    title: 'Presets',
    subtitle: 'Profile und Vorlagen.',
    companionVariant: 'base',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  security: {
    id: 'security',
    title: 'Sicherheit',
    subtitle: 'Firewall und Härtung.',
    companionVariant: 'security',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  users: {
    id: 'users',
    title: 'Benutzer',
    subtitle: 'Konten verwalten.',
    companionVariant: 'base',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  'control-center': {
    id: 'control-center',
    title: 'Control Center',
    subtitle: 'Viele Expertenmodule auf einen Blick.',
    companionVariant: 'debug',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: true,
  },
  'periphery-scan': {
    id: 'periphery-scan',
    title: 'Peripherie-Scan',
    subtitle: 'Hardware erkennen.',
    companionVariant: 'debug',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  webserver: {
    id: 'webserver',
    title: 'Webserver',
    subtitle: 'HTTP-Dienste.',
    companionVariant: 'base',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  nas: {
    id: 'nas',
    title: 'NAS',
    subtitle: 'Netzwerkspeicher.',
    companionVariant: 'base',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  homeautomation: {
    id: 'homeautomation',
    title: 'Hausautomation',
    subtitle: 'Smart Home.',
    companionVariant: 'base',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  musicbox: {
    id: 'musicbox',
    title: 'Musikbox',
    subtitle: 'Audio-Setup.',
    companionVariant: 'base',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  'kino-streaming': {
    id: 'kino-streaming',
    title: 'Kino / Streaming',
    subtitle: 'Medien-Setup.',
    companionVariant: 'base',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  learning: {
    id: 'learning',
    title: 'Lernen',
    subtitle: 'Tutorials und Vertiefung.',
    companionVariant: 'tutorial',
    beginnerVisible: false,
    availability: 'coming_later',
    trafficLightState: 'unknown',
    lockedForBeginner: false,
    comingLater: true,
  },
  devenv: {
    id: 'devenv',
    title: 'Entwicklung',
    subtitle: 'Nur für Entwickler.',
    companionVariant: 'debug',
    beginnerVisible: false,
    availability: 'locked',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  mailserver: {
    id: 'mailserver',
    title: 'Mailserver',
    subtitle: 'Nur für Entwickler.',
    companionVariant: 'security',
    beginnerVisible: false,
    availability: 'locked',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  'raspberry-pi-config': {
    id: 'raspberry-pi-config',
    title: 'Raspberry Pi',
    subtitle: 'Pi-spezifische Optionen.',
    companionVariant: 'base',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  'pi-installer-update': {
    id: 'pi-installer-update',
    title: 'SetupHelfer Update',
    subtitle: 'Experten-Build.',
    companionVariant: 'install',
    beginnerVisible: false,
    availability: 'advanced_only',
    trafficLightState: 'unknown',
    lockedForBeginner: true,
    comingLater: false,
  },
  'dsi-radio-settings': {
    id: 'dsi-radio-settings',
    title: 'DSI Radio',
    subtitle: 'Display-Radio.',
    companionVariant: 'base',
    beginnerVisible: false,
    availability: 'available',
    trafficLightState: 'unknown',
    lockedForBeginner: false,
    comingLater: false,
  },
  tft: {
    id: 'tft',
    title: 'TFT',
    subtitle: 'Touch-Display.',
    companionVariant: 'base',
    beginnerVisible: false,
    availability: 'available',
    trafficLightState: 'unknown',
    lockedForBeginner: false,
    comingLater: false,
  },
}

export function getModuleDefinition(id: string): BeginnerModuleDefinition | undefined {
  return MODULE_DEFINITIONS[id as ModuleId]
}

export function isModuleId(id: string): id is ModuleId {
  return id in MODULE_DEFINITIONS
}

/** App-Store: Metadaten pro App-ID (Einsteiger-Reihenfolge & Markierung). */
export type AppStoreBeginnerTier = 'recommended' | 'standard' | 'advanced_later'

export interface AppStoreBeginnerMeta {
  appId: string
  tier: AppStoreBeginnerTier
  availability: AvailabilityState
  note?: string
}

export const APP_STORE_BEGINNER_META: Record<string, AppStoreBeginnerMeta> = {
  'home-assistant': {
    appId: 'home-assistant',
    tier: 'recommended',
    availability: 'available',
    note: 'Guter Einstieg ins Smart Home.',
  },
  'nextcloud': {
    appId: 'nextcloud',
    tier: 'standard',
    availability: 'available',
    note: 'Etwas mehr Planung: Nutzer, Speicher, Zugriff.',
  },
  'pi-hole': {
    appId: 'pi-hole',
    tier: 'advanced_later',
    availability: 'coming_later',
    note: 'Wirkt aufs ganze Netz – sinnvoll nach Basis-Setup.',
  },
}

export function getAppStoreBeginnerMeta(appId: string): AppStoreBeginnerMeta {
  return (
    APP_STORE_BEGINNER_META[appId] ?? {
      appId,
      tier: 'standard',
      availability: 'available',
    }
  )
}
