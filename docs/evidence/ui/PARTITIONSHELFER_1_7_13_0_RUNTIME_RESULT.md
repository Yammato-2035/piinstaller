# Partitionshelfer 1.7.13.0 – Post-Deploy Runtime Result

**Datum:** 2026-06-10  
**HEAD:** `145fbbb` (Feature-Commits: `5d65709`, Evidence: `99969d7`/`145fbbb`)  
**Deploy:** erfolgreich nach `/opt`

## Phase 0 – Version / Services

| Prüfung | Ergebnis |
|---------|----------|
| `setuphelfer-backend.service` | `active` |
| `setuphelfer.service` | `active` |
| `GET /api/version` → `project_version` | **`1.7.13.0`** |

## Phase 1 – Gates

| Gate | Exit | Bewertung |
|------|------|-----------|
| `check-runtime-profile-deploy-gate.sh` | **0** | OK (profile-aware) |
| Legacy-Hinweis im Profil-Gate | 20 | **informational only** — kein Blocker |
| `check-runtime-deploy-gate.sh` | 20 | Legacy — dev-dashboard 404 erwartet in `release` |
| `check-backend-version-gate.sh` | **0** | OK |
| `check-packaging-version-gate.sh` | 0 | WARN stale_bundle (informational) |

## Phase 2 – Storage Role API Smoke

Rohdaten: `/tmp/partitions_scan_1_7_13_0.json`, `/tmp/storage_roles_1_7_13_0.json`

| Gerät | Modell | Rolle | Confidence | write_allowed | risk |
|-------|--------|-------|------------|---------------|------|
| `/dev/nvme1n1` | Samsung 980 PRO | **windows_system_disk** | high | false | red |
| `/dev/nvme0n1` | Samsung 980 PRO | **linux_system_disk** | high | false | red |
| `/dev/sda` | HGST HTS7210 | linux_system_disk | medium | false | red |
| `/dev/sdb` | Ultra Line (Intenso) | **rescue_stick** | high | false | red |

### Pflichtprüfung

| Kriterium | Ergebnis |
|-----------|----------|
| `nvme1n1` = Windows-System | **JA** — EFI + NTFS + Microsoft Basic Data + Recovery |
| `nvme0n1` = Linux-System | **JA** — live root `/`, EFI, ext4 |
| Rettungsstick erkannt | **JA** (`sdb`) — Evidence `rescue_stick_markers_detected` (nach Deploy verifizieren, ggf. Review) |
| `write_allowed=false` System/Rescue | **JA** — alle 4 Datenträger |
| Unbekannte nicht grün | **JA** — kein `green`/`unknown_disk` mit Freigabe |

`GET /api/partitions/storage-roles` → **HTTP 200**, 4 Einträge konsistent mit Scan.

## Phase 3 – Hardstop Preview

| Ziel | status | write_allowed | Hardstops |
|------|--------|---------------|-----------|
| `/dev/nvme1n1` | blocked | false | `partition.hardstop.target_is_windows_system_disk` |
| `/dev/nvme0n1` | blocked | false | `partition.hardstop.target_is_linux_system_disk` |
| `/dev/sdb` | blocked | false | `partition.hardstop.target_is_rescue_stick` |

Keine grüne Freigabe für Systemlaufwerke.

## Phase 4 – UI Sichtprüfung

**URL:** `http://127.0.0.1:3001/?page=partitions`  
**Bundle `/opt`:** enthält `partition-tool-shell`, `Setuphelfer Partitionshelfer`, `windows_system_disk`, `partition-toggle-technical-details`

| Kriterium | Sichtbar |
|-----------|----------|
| Version v1.7.13.0 im Tool-Chrome | **JA** |
| Logo / Tool-Shell | **JA** |
| „Zurück zum Setuphelfer“ | **JA** |
| Read-only Badge | **JA** |
| Windows-NVMe als Windows-Systemlaufwerk | **JA** |
| Linux-NVMe blockiert | **JA** |
| `write_allowed false` im Sicherheitspanel | **JA** |
| Keine Schreibbuttons | **JA** |
| Professioneller Werkzeugrahmen vs. 1.7.12.x | **JA** |

**Screenshot:** `docs/evidence/ui/PARTITIONSHELFER_1_7_13_0_RUNTIME_SCREENSHOT.png` (Chrome headless, 1600×1200, 8s virtual-time-budget)

**Hinweis UI:** Beim ersten Laden erscheint der **Systemcheck-Modal** über der Partitionsansicht — schließt sich mit „Weiter“. Kein Blocker für Partitionshelfer-Funktion.

## Bekannte Abweichungen / fachliche Mängel

| Punkt | Beschreibung |
|-------|--------------|
| `sda` Backup-HDD | Als `linux_system_disk` klassifiziert (ext4/GPT), obwohl nur Backup-Mount — **Review** |
| `sdb` Intenso USB | Als `rescue_stick` klassifiziert — vermutlich False-Positive (nur EFI vfat) — **Review** |
| Systemcheck-Modal | Überlagert Partitionshelfer beim ersten Besuch |
| Mockup | Globale Sidebar/Footer bleiben App-Chrome |

## Offene Punkte

1. Klassifikation `sda`/`sdb` verfeinern (separater Auftrag, kein Hotfix in dieser Validation)
2. Systemcheck-Modal für `?page=partitions` optional unterdrücken
3. Manueller Hard-Reload ohne Modal für Marketing-Screenshot

## Constraints

- Nur Read-only Prüfung
- Kein Code-Fix in dieser Session
- Kein `git add -A`
