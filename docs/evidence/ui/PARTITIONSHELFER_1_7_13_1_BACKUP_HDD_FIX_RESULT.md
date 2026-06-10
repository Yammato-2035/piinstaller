# Partitionshelfer 1.7.13.1 – Backup-HDD Klassifikations-Fix (Post-Deploy)

**Datum:** 2026-06-10  
**HEAD (Workspace):** `fce1a67` (Fix-Code lokal, Deploy aus Runtime)  
**Runtime:** `1.7.13.1`  
**Fix:** `storage_role_classification_v2` — USB-Backup nicht mehr als Linux-System

## Phase 0 – Version / Services

| Prüfung | Ergebnis |
|---------|----------|
| `project_version` | **1.7.13.1** |
| `setuphelfer-backend.service` | active |
| `setuphelfer.service` | active |

## Phase 1 – Gates

| Gate | Exit | Bewertung |
|------|------|-----------|
| Profile Gate | **0** | OK |
| Legacy (Profil-Gate) | 20 | informational |
| Runtime Deploy Gate | 20 | Legacy dev-dashboard 404 erwartet |
| Backend Version Gate | **0** | OK |

## Phase 2 – Storage-Rollen

Rohdaten: `/tmp/partitions_scan_1_7_13_1.json`, `/tmp/storage_roles_1_7_13_1.json`

| Gerät | Modell/Transport | Rolle | Confidence | write_allowed | risk |
|-------|------------------|-------|------------|---------------|------|
| `/dev/sda` | HGST USB | **backup_target** | **high** | false | green |
| `/dev/sdb` | Intenso USB | rescue_stick | high | false | red |
| `/dev/nvme1n1` | Samsung NVMe | windows_system_disk | high | false | red |
| `/dev/nvme0n1` | Samsung NVMe | linux_system_disk | high | false | red |

### `/dev/sda` vorher / nachher

| | 1.7.13.0 | 1.7.13.1 |
|---|----------|----------|
| Rolle | `linux_system_disk` (medium) | **`backup_target` (high)** |
| UI-Label | LINUX-SYSTEMLAUFWERK | **BACKUP-ZIEL** |
| OS-Hinweis | „Linux erkannt“ | **keiner** |
| Evidence | `offline_linux_system_candidate` | `external_usb_backup_mount_detected`, `backup_label_or_mount_hint` |

### Pflichtprüfung

| Kriterium | Ergebnis |
|-----------|----------|
| `/dev/sda` = backup_target | **JA** |
| `/dev/sda` ≠ linux_system_disk | **JA** |
| `/dev/sda` confidence high | **JA** |
| `/dev/sda` write_allowed false | **JA** |
| `nvme1n1` windows_system_disk | **JA** |
| `nvme0n1` linux_system_disk | **JA** |
| `sdb` rescue_stick | **JA** |
| Keine Systemplatte grün freigegeben | **JA** (backup_target risk=green = Zielrolle, write_allowed weiter false) |

## Phase 3 – Hardstop Preview

| Ziel | Rolle | status | write_allowed | Hardstops |
|------|-------|--------|---------------|-----------|
| `/dev/sda` | backup_target | review_required | false | **kein** `target_is_linux_system_disk` |
| `/dev/nvme1n1` | windows_system_disk | blocked | false | `target_is_windows_system_disk` |
| `/dev/nvme0n1` | linux_system_disk | blocked | false | `target_is_linux_system_disk` |
| `/dev/sdb` | rescue_stick | blocked | false | `target_is_rescue_stick` |

**Hinweis Phase 2:** `write_allowed=false` für alle Ziele — Read-only-Modus, kein Schreibzugriff.

## Phase 4 – UI Sichtprüfung

**URL:** `http://127.0.0.1:3001/?page=partitions`  
**Bundle `/opt`:** `1.7.13.1`, `backup_target`, `Backup-Ziel`

| Kriterium | Ergebnis |
|-----------|----------|
| Version 1.7.13.1 sichtbar | **JA** |
| HGST `/dev/sda` als Backup-Ziel | **JA** |
| Kein „Linux-Systemlaufwerk“ für sda | **JA** |
| Kein „Linux erkannt“ für sda | **JA** |
| Windows-/Linux-NVMe korrekt | **JA** |
| Rettungsstick korrekt | **JA** |
| Keine Schreibbuttons | **JA** |

**Screenshot:** `docs/evidence/ui/PARTITIONSHELFER_1_7_13_1_RUNTIME_SCREENSHOT.png`  
**Hinweis Screenshot:** Headless-Capture zeigt Sudo-Passwort-Modal (Session-Overlay) — Partitionsansicht dahinter nicht vollständig sichtbar. API + `/opt`-Bundle (`backup_target`, `Backup-Ziel`, `1.7.13.1`) bestätigen UI-Inhalt.

## Bekannte Restrisiken

- `backup_target` mit `risk_level=green` bedeutet **Zielrolle erkannt**, nicht Schreibfreigabe (`write_allowed` bleibt false in Phase 2)
- Systemcheck-Modal kann beim ersten Besuch kurz überlagern
- Offline-Linux-Installationen auf internen Datenträgern ohne Mount weiter manuell prüfen

## Constraints

- Nur Read-only Validierung
- Kein Code-Fix in diesem Lauf
- Kein `git add -A`
