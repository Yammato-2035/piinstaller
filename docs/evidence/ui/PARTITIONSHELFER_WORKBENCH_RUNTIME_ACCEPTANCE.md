# Partitionshelfer Workbench – Runtime Acceptance (Phase 3.1)

**Datum:** 2026-06-10  
**HEAD vorher:** `3266d8f`  
**Workbench-Commit:** `cd15bac` — *Add partition helper workbench UI*  
**Workspace-Version:** `1.7.13.2`  
**Runtime-Version (API):** `1.7.13.1` (Deploy ausstehend)

## Phase 0 – Statusprüfung

| | Wert |
|---|------|
| Branch | `main` |
| Version | `1.7.13.2` |

**Hinweis:** Workspace enthält **viele fremde** uncommitted Änderungen (Rescue, DCC, Backend-Governance, …).  
**Nur Workbench-Dateien** wurden gestaged/committed (14 Dateien). Kein `git add -A`.

### Fremde Änderungen (nicht committed)

- `backend/runtime_governance/route_exposure.py`
- `backend/tests/test_*` (Rescue/Profile)
- `build/rescue/live-build/*`
- diverse `docs/evidence/rescue`, `docs/evidence/dev-dashboard`
- `frontend/src/pages/DevelopmentDashboard.tsx`, `RaspberryPiConfig.tsx`, Rescue-Dateien
- `packaging/`, `scripts/rescue-live/*`

## Phase 1–3 – Staging, Tests, Commit

| Schritt | Ergebnis |
|---------|----------|
| Staged | 14 Workbench-Dateien (siehe Commit) |
| Tests `PartitionManagerPhase2` | **17/17** |
| Build | **OK** |
| Commit | `cd15bac` |

## Phase 4 – Deploy

| Schritt | Ergebnis |
|---------|----------|
| `sudo ./scripts/deploy-to-opt.sh` | **BLOCKIERT** — sudo-Passwort in Agent-Session nicht verfügbar |
| `setuphelfer-backend.service` | active |
| `setuphelfer.service` | active |
| Bundle `:3001` | `index-dS9YjSk4.js` — **kein** `partition-workbench` String |
| API `project_version` | **1.7.13.1** |

**Operator-Aktion erforderlich:**

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
```

Danach Hard Reload `http://127.0.0.1:3001/?page=partitions`

## Phase 5 – Gates

| Gate | Exit | Bewertung |
|------|------|-----------|
| Profile Gate | 12 | Drift Workspace `1.7.13.2` ≠ Runtime `1.7.13.1` |
| Backend Version Gate | 14 | gleicher Drift |
| Legacy Runtime Deploy Gate | 20 | dev-dashboard 404 — **informational** |

## Phase 6 – Storage-Rollen (unverändert)

| Gerät | Rolle | Confidence |
|-------|-------|------------|
| `/dev/nvme1n1` | windows_system_disk | high |
| `/dev/nvme0n1` | linux_system_disk | high |
| `/dev/sda` | backup_target | high |
| `/dev/sdb` | rescue_stick | high |

Keine Änderung gegenüber 1.7.13.1.

## Phase 7 – Sichtprüfung `:3001` (Ist nach Screenshot)

**Status: Workbench NICHT aktiv** — altes 3-Spalten-Layout (`PartitionToolShell`), Systemcheck-Modal sichtbar.

| Kriterium | Erwartet | Ist (:3001) |
|-----------|----------|-------------|
| Workbench-Header | ✓ | ✗ (altes Layout) |
| Sidebar links | ✓ | ✗ (Karten-Grid) |
| Hardstop Center | ✓ | ✗ |
| Expertenmodus unten | ✓ | ✗ |
| Datenträger geladen | ✓ | ✓ (2 NVMe sichtbar) |
| Read-only | ✓ | ✓ |
| Keine Schreibbuttons | ✓ | ✓ |

## Phase 8 – Runtime-Screenshots

| Datei | Port | Inhalt |
|-------|------|--------|
| `PARTITIONSHELFER_WORKBENCH_RUNTIME_1_7_13_2.png` | **3001** | Pre-Workbench-Bundle (1.7.13.1) |
| `PARTITIONSHELFER_WORKBENCH_RUNTIME_DETAIL_1_7_13_2.png` | **3001** | Detail-Capture |

Nach Deploy erneut erfassen empfohlen.

## Bewertung (vor Deploy — Workbench nicht in Runtime)

| Bereich | Bewertung |
|---------|-----------|
| Werkzeuggefühl | **Ausstehend** (Commit OK, Runtime alt) |
| Übersicht | **Ausstehend** |
| Datenträgerauswahl | **Teilweise** (API/alt-UI zeigt Disks) |
| Sicherheitsstatus | **OK** (Panel sichtbar im Alt-Layout) |
| Hardstop Center | **Ausstehend** (nur im neuen Bundle) |
| Restore-Vorschau | **Teilweise** (Alt-Layout) |
| Expertenmodus | **Ausstehend** |
| Gesamteindruck | **BLOCKIERT bis Deploy** |

## Top 5 Verbesserungen für Phase 3.2

1. **Vollbild-Workbench** — globale App-Sidebar optional ausblenden auf `?page=partitions`
2. **Sidebar-Dichte** — kompaktere Geräteliste bei >4 Datenträgern
3. **Hardstop Center** — Evidence-Gründe direkt aus Backend-`evidence[]` statt statischer Map
4. **Cockpit-Konsolidierung** — doppelte Mini-Karten im Safety-Panel reduzieren
5. **Runtime-Screenshot-Pipeline** — automatisierter Capture nach Deploy-Gate (Port 3001)

## Explizite Bestätigung

| Prüfpunkt | Status |
|-----------|--------|
| Workbench-Commit in Git | **JA** (`cd15bac`) |
| Workbench in Runtime `:3001` aktiv | **NEIN** (Deploy blockiert) |
| Storage-Rollen unverändert | **JA** |
| Keine Klassifikations-/Hardstop-Änderung | **JA** |
| Keine Schreibfunktion | **JA** |
| Kein Queue Apply / Restore Execute | **JA** |

**Gesamt:** Runtime-Abnahme **nicht bestanden** — Deploy durch Operator erforderlich, danach Phase 3.1 wiederholen.
