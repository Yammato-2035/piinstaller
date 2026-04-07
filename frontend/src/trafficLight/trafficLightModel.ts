/**
 * Zentrales Ampelmodell (Sicherheit, Reifegrad, Verfügbarkeit, Orientierung).
 * UI-Texte und Semantik nur hier bündeln – nicht auf den Seiten zerstreuen.
 *
 * TRAFFIC_LIGHT_PAGE_ROLES (Zuordnung):
 * - AppStore: Ampel = Verfügbarkeit / Eignung zur Installation (grün direkt, gelb später/Voraussetzungen, rot nicht empfohlen).
 * - BackupRestore: Ampel = Freigabelage / Restrisiko (Phase 3/4): standardmäßig gelb (Kern nicht verifiziert), rot bei Blockern/Risiko; grün nur mit nachgewiesenen Nachweisen (aktuell im UI nicht freigeschaltet).
 * - MonitoringDashboard: Ampel = Betriebsbereitschaft der Stack-Komponenten + Gesamt (grün läuft, gelb installiert aber gestoppt/fehlend, rot kritisch).
 *
 * TODO Backup: Sobald `GET /api/system/status` mit persistiertem realtest_state / last_verify_ok zuverlässig im Frontend angebunden ist,
 * deriveBackupSafetyTrafficLight darauf umstellen statt der aktuellen UI-Zustands-Heuristik.
 */

import type { DiagnosisRecord } from '../types/diagnosis'

/** Aktive Lampe (Backend-Dashboard nutzt dieselben Literal-Strings). */
export type TrafficLightLampState = 'green' | 'yellow' | 'red'

/** Inkl. unbekannt – UI zeigt „vorsichtig gelb“, bis Daten da sind. */
export type TrafficLightState = TrafficLightLampState | 'unknown'

/** Semantik Sicherheit Backup/Restore (Datenquelle später: Verify-Ergebnis, Diagnose, realtest_state). */
export type SafetyState = 'verified_ok' | 'uncertain' | 'risky'

/** Semantik App-Store (Eignung, nicht nur installiert). */
export type AvailabilitySignal = 'direct_suitable' | 'later_or_prerequisites' | 'unavailable_or_discouraged'

export const TRAFFIC_LIGHT_COPY = {
  appStore: {
    direct_suitable: {
      label: 'Direkt geeignet',
      detail: 'Für dein Profil als sinnvoll erreichbar bzw. bereits installiert.',
    },
    later_or_prerequisites: {
      label: 'Später / mit Voraussetzungen',
      detail: 'Braucht mehr Planung, Netz-Kontext oder ist für später vorgesehen.',
    },
    unavailable_or_discouraged: {
      label: 'Nicht empfohlen / blockiert',
      detail: 'Noch nicht verfügbar, gesperrt oder für Einsteiger nicht die erste Wahl.',
    },
  },
  backup: {
    verified_calm: {
      label: 'Backup-Sicherheit',
      detail: 'Keine offene Verify-/Diagnose-Warnung; Restore-Vorschau nicht aktiv.',
    },
    verifying_or_unclear: {
      label: 'Prüfung läuft oder unklar',
      detail: 'Verify aktiv oder Zwischenzustand – Ergebnis abwarten bzw. Hinweise lesen.',
    },
    diagnosis_or_restore_risk: {
      label: 'Risiko / Prüfung nötig',
      detail: 'Verify/Diagnose meldet Problem oder Restore-Vorschau – Daten können betroffen sein.',
    },
    core_unverified: {
      label: 'Kernfunktion nicht verifiziert',
      detail: 'Teilfunktionen sind geprüft, ein erfolgreicher Backup-Lauf ist nicht nachgewiesen.',
    },
    runtime_blocked_sudo: {
      label: 'Laufzeit blockiert',
      detail: 'Backup-Lauf ist aktuell blockiert (Sudo erforderlich).',
    },
  },
  monitoring: {
    stack_ok: {
      label: 'Überwachung betriebsbereit',
      detail: 'Ausgewählte Komponenten installiert und laufen.',
    },
    stack_partial: {
      label: 'Teilweise eingerichtet',
      detail: 'Mindestens eine Komponente installiert, aber nicht alles aktiv oder Stack unvollständig.',
    },
    stack_off: {
      label: 'Monitoring nicht aktiv',
      detail: 'Stack nicht installiert oder nicht erreichbar – Einrichtung optional.',
    },
    prometheus: { label: 'Prometheus', detail: 'Metriken-Server' },
    grafana: { label: 'Grafana', detail: 'Visualisierung' },
    node_exporter: { label: 'Node Exporter', detail: 'System-Metriken' },
  },
} as const

export type AppStoreCopyKey = keyof typeof TRAFFIC_LIGHT_COPY.appStore
export type BackupCopyKey = keyof typeof TRAFFIC_LIGHT_COPY.backup
export type MonitoringCopyKey = keyof typeof TRAFFIC_LIGHT_COPY.monitoring

/** LampTriState-Reihenfolge: schlechteste gewinnt. */
const LAMP_RANK: Record<TrafficLightLampState, number> = { red: 0, yellow: 1, green: 2 }

export function worstTrafficLightLamp(lamps: TrafficLightLampState[]): TrafficLightLampState {
  if (lamps.length === 0) return 'yellow'
  return lamps.reduce((a, b) => (LAMP_RANK[a] <= LAMP_RANK[b] ? a : b))
}

export function trafficLightStateToLamp(state: TrafficLightState): TrafficLightLampState {
  if (state === 'unknown') return 'yellow'
  return state
}

/** Gleiche Werte wie `AppStoreBeginnerMeta` / `AvailabilityState` – hier dupliziert, um Zyklen mit moduleModel zu vermeiden. */
export type AppStoreTrafficMeta = {
  tier: 'recommended' | 'standard' | 'advanced_later'
  availability: 'available' | 'locked' | 'coming_later' | 'advanced_only'
}

export function deriveAppStoreTrafficLight(
  meta: AppStoreTrafficMeta,
  installed: boolean
): { lamp: TrafficLightLampState; signal: AvailabilitySignal; copyKey: AppStoreCopyKey } {
  if (installed) {
    return { lamp: 'green', signal: 'direct_suitable', copyKey: 'direct_suitable' }
  }
  if (meta.availability === 'locked') {
    return { lamp: 'red', signal: 'unavailable_or_discouraged', copyKey: 'unavailable_or_discouraged' }
  }
  if (meta.availability === 'coming_later') {
    return { lamp: 'yellow', signal: 'later_or_prerequisites', copyKey: 'later_or_prerequisites' }
  }
  if (meta.tier === 'recommended') {
    return { lamp: 'green', signal: 'direct_suitable', copyKey: 'direct_suitable' }
  }
  if (meta.tier === 'advanced_later') {
    return { lamp: 'yellow', signal: 'later_or_prerequisites', copyKey: 'later_or_prerequisites' }
  }
  return { lamp: 'yellow', signal: 'later_or_prerequisites', copyKey: 'later_or_prerequisites' }
}

function diagnosisToLamp(d: DiagnosisRecord | null): TrafficLightLampState | null {
  if (!d) return null
  if (d.companion_mode === 'blocked') return 'red'
  if (d.severity === 'critical' || d.severity === 'high') return 'red'
  if (d.severity === 'medium') return 'yellow'
  return 'yellow'
}

export function deriveBackupSafetyTrafficLight(input: {
  verifyDiagnosis: DiagnosisRecord | null
  anyVerifying: boolean
  hasRestorePreview: boolean
  hasRealBackupVerification: boolean
  sawSudoRequired: boolean
}): { lamp: TrafficLightLampState; copyKey: BackupCopyKey } {
  const fromDx = diagnosisToLamp(input.verifyDiagnosis)
  if (input.sawSudoRequired) {
    return { lamp: 'red', copyKey: 'runtime_blocked_sudo' }
  }
  if (fromDx === 'red' || input.hasRestorePreview) {
    return { lamp: 'red', copyKey: 'diagnosis_or_restore_risk' }
  }
  if (!input.hasRealBackupVerification) {
    return { lamp: 'yellow', copyKey: 'core_unverified' }
  }
  if (fromDx === 'yellow' || input.anyVerifying) {
    return { lamp: 'yellow', copyKey: 'verifying_or_unclear' }
  }
  return { lamp: 'green', copyKey: 'verified_calm' }
}

export function deriveMonitoringComponentLamp(installed: boolean, running: boolean): TrafficLightLampState {
  if (installed && running) return 'green'
  if (installed && !running) return 'yellow'
  return 'yellow'
}

export function deriveMonitoringOverallTrafficLight(status: {
  prometheus?: { installed?: boolean; running?: boolean }
  grafana?: { installed?: boolean; running?: boolean }
  node_exporter?: { installed?: boolean; running?: boolean }
} | null): { lamp: TrafficLightLampState; copyKey: MonitoringCopyKey } {
  if (!status) {
    return { lamp: 'yellow', copyKey: 'stack_partial' }
  }
  const parts = ['prometheus', 'grafana', 'node_exporter'] as const
  const lamps = parts.map((k) => {
    const s = status[k]
    return deriveMonitoringComponentLamp(!!s?.installed, !!s?.running)
  })
  const worst = worstTrafficLightLamp(lamps)
  const anyInstalled = parts.some((k) => status[k]?.installed)
  const allRunning = parts.every((k) => {
    const s = status[k]
    return !s?.installed || s?.running
  })
  if (anyInstalled && allRunning && lamps.every((l) => l === 'green')) {
    return { lamp: 'green', copyKey: 'stack_ok' }
  }
  if (!anyInstalled) {
    return { lamp: 'yellow', copyKey: 'stack_off' }
  }
  return { lamp: worst, copyKey: 'stack_partial' }
}
