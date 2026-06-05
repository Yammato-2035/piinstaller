# Windows 11 Rescue — Operator Readonly Scan Handoff

**Track:** `windows-laptop-rescue-inspect`  
**Ziel-Hardware:** 2×2 TB NVMe, AMD Ryzen, NVIDIA GPU, Windows 11 Pro (später stable + Linux Mint Dualboot)  
**Modus:** read-only — kein Schreiben, kein Mount ohne BitLocker-OK

## 1. Voraussetzungen

- Setuphelfer Rescue-Stick gebootet (späterer Lauf — nicht in diesem Workspace-Stub)
- Netzwerk für Telemetrie-ACK (oder lokale Queue + gelber Status)
- Operator-Terminal auf dem Stick
- Skript: `scripts/windows-rescue/plan-windows-readonly-inspect.sh`

## 2. Sicherheitsgrenzen

| Verboten | Erlaubt |
|----------|---------|
| NTFS-write, chkdsk /f, bcdboot, DISM/SFC | lsblk/blkid read-only |
| BitLocker-Unlock, manage-bde | BitLocker-Status dokumentieren |
| Cloud-Credentials im Repo | Telemetrie nur diagnostic_metadata |
| Partitionieren, Bootloader schreiben | Planungsberichte |

## 3. BitLocker zuerst prüfen

- Status **niemals annehmen** — `unknown` blockiert Dateizugriff
- Codes: `WIN-BITLOCKER-UNKNOWN`, `WIN-BITLOCKER-LOCKED`, `WIN-BITLOCKER-001`…`006`
- Locked → keine Dateisicherung, keine Registry aus geschütztem Volume

## 4. Read-only Mount nur nach BitLocker-OK

```bash
bash scripts/windows-rescue/plan-windows-readonly-inspect.sh /tmp/windows-readonly-plan.json
```

- Ausgabe prüfen: `blocked_reasons`, `readonly_mount_plan`, `forbidden`
- **Kein** automatisches `mount` aus diesem Skript

## 5. Hardware erfassen

- CPU: AMD Ryzen (Vendor/Model)
- GPU: NVIDIA
- NVMe: 2× ~2 TB — Code `WIN-STORAGE-003` bei Dual-NVMe-Review

## 6. Windows-Partitionen klassifizieren

- EFI-Kandidaten, NTFS/Windows-Kandidaten, Linux-Kandidaten
- Codes: `WIN-STORAGE-001`, `WIN-STORAGE-002`

## 7. Explorer-/Shell-Fehler prüfen

- Nur nach BitLocker-OK und read-only Mount
- Codes: `WIN-SHELL-001`, `WIN-EXPLORER-001`, `WIN-EXPLORER-002`

## 8. Backup-Auswahl nur Dry-Run

- `backup_selection.dry_run_only=true`
- Keine Cloud-Tokens, kein Upload
- Code: `WIN-BACKUP-001`

## 9. Telemetrie-Report erzeugen

- Backend-Stub: `backend/core/windows_rescue_inspect.py`
- Envelope: Hash über Report, POST laut `docs/architecture/WINDOWS_RESCUE_TELEMETRY_SERVER_CONTRACT.md`

## 10. Telemetrie-ACK prüfen

- Pflicht: `ack_status=acknowledged`, `server_ack_id`, Hash-Match
- Codes: `WIN-TELEMETRY-001`, `WIN-TELEMETRY-002`
- Kein Grün ohne ACK

## 11. Keine Repartition ohne

- [ ] Backup-Manifest verifiziert
- [ ] Telemetrie ACK + Hash-Match
- [ ] Operator-Freigabe
- [ ] Ziel-Disk-Plan reviewed  
- Code: `WIN-REPARTITION-001`

## 12. Kein Bootloader-Schreiben in diesem Track

- Dualboot nur Planung: Windows 11 Pro stable + Linux Mint
- Code: `WIN-DUALBOOT-001`, `WIN-BOOTLOADER-001`

## Evidence / Schema

- Sample: `docs/evidence/windows-rescue/windows_inspect_operator_readonly_sample.json`
- Telemetrie: `docs/evidence/windows-rescue/windows_rescue_telemetry.schema.json`
- Next Prompt nach Stub: `WINDOWS11_RESCUE_OPERATOR_HARDWARE_READONLY_RUN`
