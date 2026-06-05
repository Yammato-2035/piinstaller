# Windows Laptop Rescue Inspect — Plan

**Track-ID:** `windows-laptop-rescue-inspect`  
**Priorität:** P1  
**Status:** planned / yellow  
**Next Prompt:** `WINDOWS11_RESCUE_INSPECT_MVP`  
**Evidence-Level:** `planning_only`

## Nutzerbedarf

Rettungsstick für Windows-11-Pro-Laptop (Beta/Insider möglich): read-only Inspect, strukturierte Daten, Dashboard-Anzeige, Fehlererkennung, Backup-Planung (Dry-Run), Dualboot-Vorbereitung (nur Plan).

## Milestones

1. **windows11-readonly-detection** — GPT/UEFI/NTFS/BitLocker/Mount-Plan
2. **windows11-system-inventory** — Offline-Registry, Profile, Boot-Hinweise
3. **windows11-fault-detection** — explorer.exe, Shell/Userinit, Logs indexieren
4. **windows11-guided-remediation-suggestions** — Codes only, no actions
5. **windows11-selective-cloud-backup-planning** — Auswahlmodell, Manifest, Dry-Run
6. **windows11-dualboot-preparation** — Planungsbericht only

## Harte rote Linien

Kein NTFS-write, kein chkdsk /f, kein bcdboot, kein DISM/SFC gegen Ziel, kein Cloud-Upload mit Credentials, kein Partitionieren.

## Abgrenzung

Separater Track — nicht Restore/USB-Write/Monolith/Controlled Runner.
