# Rescue ISO — Runtime Integration Rebuild Result (Ingest)

**Klassifikation:** `runtime_integration_rebuild_success_validator_green`  
**Rescue ISO Runtime Integration:** **partial_green**  
**Rescue gesamt:** **yellow** (kein VM/USB/Restore-Nachweis)

## Operator Ground Truth

| Feld | Wert |
|------|------|
| Freigabe | `RESCUE_RUNTIME_REBUILD_FREIGEGEBEN=1` |
| Ende | `[2026-05-29 16:01:46] lb_source` |
| **LB_EXIT** | **0** |
| Summary | `controlled_iso_build_latest_summary.json` |
| Validator | **Exit 0** — bundle, enabled units, DE keyboard/locale, login hints |

## Neues ISO

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| mtime | 2026-05-29 16:01:45 |
| Größe | 509607936 bytes (~486 MB) |
| SHA256 | `3731d1230a27ad2a3981c310611e0c6217c8b04e85112cea49559aaf88e4cdb5` |
| Volume | `SETUPHELFER_RESCUE` |

## Vorherige ISO (Referenz)

| Feld | Wert |
|------|------|
| mtime | 2026-05-29 13:49 |
| SHA256 | `03d5aa95ba5e63f603a13bc7ec8765156aadddf3f8e7b6946c0bb08f9aba31f6` |
| Validator (alt) | Exit **12** (systemd enable fehlte) |

## Belegt im Squashfs (Validator Exit 0)

- `/opt/setuphelfer-rescue` (Bundle, venv, Frontend)
- `multi-user.target.wants` → Setuphelfer-Units
- DE-Tastatur / Locale / `Europe/Berlin`
- Login-Hinweis **user** / **live**

## Nicht ausgeführt

USB-Write, Restore, Hardwaretest, VM-Funktionstest in diesem Ingest-Lauf.

**Nächster Schritt:** `RESCUE_ISO_VISUAL_LIVE_SYSTEM_FUNCTIONAL_VALIDATION` (QEMU, Login user/live, systemctl/curl **in der VM**).

JSON: `rescue_iso_runtime_integration_rebuild_result_ingest_latest.json`
