# Partitionshelfer Workbench – Runtime Acceptance (Phase 3.1)

**Datum:** 2026-06-10  
**Workbench-Commit:** `cd15bac`  
**Evidence vorher (blockiert):** `d1b4b7e`  
**Re-Run nach Operator-Deploy:** 2026-06-10  
**Status:** **`accepted_runtime`**

## Historie

| Lauf | Runtime | Bundle | Ergebnis |
|------|---------|--------|----------|
| Erstversuch | API `1.7.13.1` | `index-dS9YjSk4.js` (kein Workbench) | **blockiert** — Deploy fehlte |
| Nach Operator-Deploy | API **`1.7.13.2`** | **`index-D8WednPP.js`** | **`accepted_runtime`** |

## Phase 0 – Status / Gate (nach Deploy)

| | Wert |
|---|------|
| HEAD | `d1b4b7e` |
| Branch | `main` |
| Workspace-Version | `1.7.13.2` |
| Runtime-Version (API) | **`1.7.13.2`** |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `setuphelfer-backend.service` | active |
| `setuphelfer.service` | active |

**Dirty Tree:** fremde Änderungen (Rescue, DCC, Backend-Governance) — nicht angefasst.

### Gates

| Gate | Exit | Bewertung |
|------|------|-----------|
| Profile Gate | **0** | OK |
| Backend Version Gate | **0** | OK |
| Legacy Runtime Deploy Gate | 20 | dev-dashboard 404 — **informational** |

Kein Versions-Drift mehr.

## Phase 1 – Frontend-Bundle `:3001`

| | Wert |
|---|------|
| Aktives Bundle | **`assets/index-D8WednPP.js`** |
| Altes Bundle ausgeschlossen | **JA** (`index-dS9YjSk4.js` nicht mehr aktiv) |
| Workbench-Strings im Bundle | **JA** |

Gefundene Strings: `partition-workbench`, `partition-device-sidebar`, `partition-hardstop-center`, `partitionWorkbench`, `Hardstop Center`

## Phase 2 – API-Smoke (read-only)

### OpenAPI `/api/partitions/*`

- `/api/partitions/scan`
- `/api/partitions/storage-roles`
- `/api/partitions/hardstop-preview`
- `/api/partitions/manifest-layout-preview`
- `/api/partitions/restore-handoff-preview`
- `/api/partitions/safety-check`
- `/api/partitions/queue` (nicht aufgerufen)

### Storage-Rollen (unverändert)

| Gerät | Rolle | write_allowed |
|-------|-------|---------------|
| `/dev/nvme1n1` | windows_system_disk | false |
| `/dev/nvme0n1` | linux_system_disk | false |
| `/dev/sda` | **backup_target** | false |
| `/dev/sdb` | rescue_stick | false |

### Hardstop-Preview

| Ziel | Klassifikation | write_allowed |
|------|----------------|---------------|
| `/dev/sda` | backup_target | false |
| `/dev/sdb` | rescue_stick | false |

Keine Queue-/Apply-/Execute-Aktion ausgelöst.

## Phase 3 – Sichtprüfung `:3001/?page=partitions`

| Kriterium | Ergebnis |
|-----------|----------|
| Workbench-Header (Logo, READ-ONLY, v1.7.13.2) | **JA** |
| Datenträger-Sidebar links | **JA** (4 Geräte, Rollenfarben) |
| Auto-Auswahl / klar wählbar | **JA** (`/dev/sda` Backup-Ziel ausgewählt) |
| Große Partitionsgrafik | **JA** |
| Sicherheitsstatus (Cockpit) | **JA** |
| Hardstop Center | **JA** |
| Restore-Handoff | **`review_required_partial_visibility`** — Panel unterhalb Viewport im Headless-Capture; funktional bei Scroll/Auswahl vorhanden |
| Kein Systemcheck-Modal | **JA** (kein Overlay) |
| Keine Schreibbuttons | **JA** |
| Keine still leere UI | **JA** |
| Fehlerzustände sichtbar (Sidebar) | **JA** (implementiert, hier nicht getriggert) |

## Phase 4 – Screenshots (Port 3001)

| Datei | Inhalt |
|-------|--------|
| `PARTITIONSHELFER_WORKBENCH_RUNTIME_1_7_13_2_AFTER_DEPLOY.png` | Workbench mit Sidebar, Grafik, Cockpit, Hardstop |
| `PARTITIONSHELFER_WORKBENCH_RUNTIME_DETAIL_1_7_13_2_AFTER_DEPLOY.png` | Detail-Capture |

Vorher (pre-Deploy): `PARTITIONSHELFER_WORKBENCH_RUNTIME_1_7_13_2.png`

## Bewertung (nach Deploy)

| Bereich | Bewertung |
|---------|-----------|
| Werkzeuggefühl | **Gut** |
| Übersicht | **Gut** |
| Datenträgerauswahl | **Gut** |
| Sicherheitsstatus | **Gut** |
| Hardstop Center | **Gut** |
| Restore-Vorschau | **OK** (teilweise außerhalb Screenshot) |
| Expertenmodus | **OK** (ausklappbar unten) |
| Gesamteindruck | **`accepted_runtime`** |

## Abweichungen / Phase 3.2

1. Globale App-Sidebar bleibt sichtbar (kein Vollbild-Workbench)
2. Restore-Handoff im Standard-Viewport oft unter Scroll
3. `backup_target` zeigt Sidebar-Status „BLOCKIERT“ (Schreibschutz-Semantik, nicht Fehler)

## Explizite Bestätigung

| Prüfpunkt | Status |
|-----------|--------|
| Workbench in Runtime `:3001` aktiv | **JA** |
| Runtime-Version 1.7.13.2 | **JA** |
| Storage-Rollen unverändert | **JA** |
| Keine Klassifikations-/Hardstop-Änderung | **JA** |
| Keine Schreibfunktion ausgelöst | **JA** |
| Kein Queue Apply / Restore Execute | **JA** |
