# Rescue Stick — Core-Abhängigkeiten

**Siehe auch:** `RESCUE_STICK_CORE_DEPENDENCIES_2026-05-20.md` (detailliertes Audit)

## Pflicht-Module (Workspace)

| Modul | Rolle |
|-------|-------|
| `core.storage_facade` | Geräte-/Mount-Erkennung |
| `core.mount_facade` | Mount-Pläne ohne Live-Root-Schreibzugriff |
| `core.safety_facade` | Ziel-Schreibfreigabe |
| `app_bootstrap.*` | Backend-Start ohne Monolith-Kopplung |

## App-Start auf Rescue-Live

Rescue-Agent optional, profilgated; kein Netzwerk-Pairing beim reinen API-Start.

## Deploy

Stick-ISO-Inhalt folgt **deployed** `/opt/setuphelfer` — Workspace-Drift blockiert Live-Diagnose bis Sync.
