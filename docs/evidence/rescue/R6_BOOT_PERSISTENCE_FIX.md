# R.6 — Boot Persistence Fix

**Datum:** 2026-06-10  
**Status:** Workspace-Fix implementiert · **Rebuild/Stick-Write/MSI-Boot ausstehend**

## Problem

Nach R.5C: Stick bootfähig, aber `/setuphelfer-evidence/` fehlt nach MSI-Boot. RS-001 Level 6 rot.

**Ursache:** Kein früher Boot-Hook — Evidence-Bundle erst am Ende des Start-Assistenten; Kiosk-Pfad (`exec ui-launch`) übersprang TUI komplett.

## Fix

| Änderung | Datei |
|----------|-------|
| `initialize_boot_evidence_marker()` | `backend/core/rescue_persistence.py` |
| `boot-init` CLI | `scripts/.../setuphelfer-rescue-evidence.py` |
| Shell-Wrapper | `scripts/.../setuphelfer-rescue-boot-evidence-init` |
| Früher Aufruf + TUI-Hinweis | `scripts/.../setuphelfer-rescue-start-assistant` |
| R6-Matrix-Einträge | `backend/core/rescue_test_matrix.py` |
| Prepare-Staging | `scripts/rescue-live/prepare-controlled-live-build-tree.sh` |
| Unit-Tests | `backend/tests/test_rescue_boot_persistence_hook_r6.py` |

## Verifikation (nach nächstem Build)

```bash
# Am Stick (MSI oder Dev-Mount nach Live-Boot):
test -f /setuphelfer-evidence/boot/boot_marker.md && echo OK
```

## Operator-Aktionen

1. Controlled ISO-Rebuild (Prepare + lb)
2. FAT32-ESP USB-Write (Operator)
3. MSI-Boot + `R6_OPERATOR_BOOT_OBSERVATION.md` ausfüllen
4. R.5C Stick-Inventory erneut

## Ampel

| Check | Vor Fix | Nach Deploy |
|-------|---------|-------------|
| boot_marker auf Stick | rot | Ziel: grün |
| Früher Hook | rot | grün (Code) |
| Operator-Beobachtung | fehlt | offen |
