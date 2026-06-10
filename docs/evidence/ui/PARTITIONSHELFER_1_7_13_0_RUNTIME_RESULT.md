# Partitionshelfer 1.7.13.0 – Runtime Result

**Datum:** 2026-06-10  
**Commit 1:** `5d65709` — `Add professional partition helper UI and storage role classification`  
**HEAD vorher:** `6b543e4`  
**Workspace-Version:** `1.7.13.0`

## Deploy

| Schritt | Ergebnis |
|---------|----------|
| `sudo ./scripts/deploy-to-opt.sh` | **BLOCKIERT** — `sudo` erfordert Passwort (kein TTY) |
| `setuphelfer-backend.service` | `active` (Runtime **1.7.12.2**) |
| `setuphelfer.service` | `active` |
| Runtime `/api/version` | `project_version: 1.7.12.2` |

**Operator-Aktion erforderlich:**

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
```

## Gates (vor Deploy, Workspace 1.7.13.0 vs Runtime 1.7.12.2)

| Gate | Ergebnis |
|------|----------|
| `check-runtime-profile-deploy-gate.sh` | Exit **12** — `project_version_mismatch:1.7.12.2!=1.7.13.0` |
| `check-runtime-deploy-gate.sh` | Legacy-Hinweis → Profil-Gate |
| `check-backend-version-gate.sh` | Exit **14** — Drift workspace `1.7.13.0` vs API `1.7.12.2` |

## Tests (vor Commit)

| Suite | Ergebnis |
|-------|----------|
| `test_storage_role_classification_windows_v1.py` + `test_partitions_phase2_safety_contracts_v1.py` | **22 passed** |
| `PartitionManagerPhase2.test.ts` | **13 passed** |
| `npm run build` | **OK** (Workspace-Bundle enthält `partitionTool`, `windows_system_disk`) |

## API-Smoke (Runtime 1.7.12.2 — alte API)

| Endpoint | Ergebnis |
|----------|----------|
| `GET /api/partitions/scan` | 4 Datenträger, **kein** `storage_role` Feld |
| `GET /api/partitions/storage-roles` | **404** (Endpoint noch nicht deployed) |
| `hardstop-preview /dev/nvme1n1` | `write_allowed=false`, **kein** `target_is_windows_system_disk` (alte Hardstop-Logik) |

Rohdaten: `/tmp/partitions_scan_1_7_13_0.json`, `/tmp/storage_roles_1_7_13_0.json`

### Erkannte Datenträger (Scan)

| Gerät | Partitionen (Kurz) |
|-------|-------------------|
| `/dev/sda` | ext4 Backup unter `/media/gabriel/Backup` |
| `/dev/sdb` | EFI vfat (Intenso USB) |
| `/dev/nvme1n1` | EFI + NTFS + Microsoft basic data + Recovery |
| `/dev/nvme0n1` | EFI + ext4 Root `/` (Linux Mint) |

### Erwartete Klassifikation nach Deploy (Engine-Simulation)

| Gerät | Rolle | Confidence | write_allowed |
|-------|-------|------------|---------------|
| `/dev/nvme0n1` | `linux_system_disk` | high | false |
| `/dev/nvme1n1` | `windows_system_disk` | high | false |
| `/dev/sda` | `backup_target` | medium | false |
| `/dev/sdb` | `external_data_disk` | low | false |

Windows-NVMe: **ja** (EFI + NTFS + Recovery + Microsoft basic data)  
Linux-System: **ja** (`nvme0n1`, Mount `/`)  
Rescue-Stick: **nein** (kein Setuphelfer-Marker)  
Backup-Ziel: **ja** (`sda`, externer Mount)

## UI-Sichtprüfung

| URL | Status |
|-----|--------|
| `http://127.0.0.1:3001/?page=partitions` | Erreichbar (HTTP 200), **altes Bundle** unter `/opt` |
| Workspace `frontend/dist` | Neues Bundle mit Tool-Shell-Strings |

**Screenshot:** `docs/evidence/ui/PARTITIONSHELFER_1_7_13_0_RUNTIME_SCREENSHOT.png` — **nicht erzeugt** (Deploy ausstehend; Port 3001 zeigt noch 1.7.12.x UI)

Manuelle Sichtprüfung nach Deploy:

1. Hard Reload + ggf. `localStorage.removeItem('pi-installer-api-base')`
2. Logo, Tool-Shell, Zurück-Button, Windows-NVMe-Karte, ausklappbare Details

## Bekannte Abweichungen vom Mockup

- App-Sidebar bleibt global (nicht Partitions-Scope)
- Exakte Pixel-Maße Design-Mockup
- Screenshot erst nach Deploy möglich

## Offene Punkte

1. Operator-Deploy mit sudo
2. Gates erneut grün prüfen
3. API-Smoke mit `storage_roles` wiederholen
4. Hardstop `target_is_windows_system_disk` auf `/dev/nvme1n1` verifizieren
5. Screenshot unter 3001 erstellen

## Constraints bestätigt

- Kein `git add -A`
- Keine fremden Dateien in Commit `5d65709`
- Keine Schreibfunktion getestet
- Safety-Gates nicht abgeschwächt
