# Deploy — Rescue Live-Runtime & Storage-Validierung (DE)

## Zweck

Nach ISO-Build und VM-Checks beschreibt diese Phase **nur read-only** Laufzeit- und Speicherfähigkeit im Rescue-Kontext: Datenträger-Inventar (`lsblk`/`blkid`), geplante **read-only**-Mounts unter `build/rescue/runtime-mounts/`, EFI-/Boot-**Analyse** (ohne Reparatur), kontrollierter Evidence-Export, Remote-Hilfe-**Planung** (ohne automatischen SSH-Start), Hardware-Matrix und ein aggregiertes **Live-Runtime-Safety-Gate**.

## API (POST)

Alle unter `/api/deploy/rescue/…` (siehe `backend/deploy/routes.py`):

- `storage-discovery`
- `readonly-mount-validation`
- `efi-boot-analysis`
- `evidence-export`
- `remote-help-preparation`
- `live-hardware-matrix`
- `live-runtime-safety-gate`

Antwortcodes folgen dem Muster `DEPLOY_RESCUE_<BEREICH>_{OK|REVIEW_REQUIRED|BLOCKED}`; das Safety-Gate nutzt `DEPLOY_RESCUE_LIVE_RUNTIME_SAFETY_GATE_OK` bei `gate_status: ready`.

## Verbote (unverändert)

Keine Partitionierung, kein `dd`/`mkfs`, kein Restore-Execute, keine EFI-/GRUB-Reparatur, kein automatischer SSH-Dienststart.

## Version

Nach erfolgreicher Abnahme auf echter Hardware (readonly) ist **1.8.0** als Zielversion denkbar; **2.0.0** bleibt für echte Recovery-Writes und breitere Plattform-Abdeckung reserviert.
