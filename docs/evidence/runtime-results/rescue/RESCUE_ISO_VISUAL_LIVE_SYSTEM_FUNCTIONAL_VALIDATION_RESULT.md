# Rescue ISO — Visual Live System Functional Validation (Handoff)

**Klassifikation:** `visual_live_functional_prepared_not_executed`  
**Grund:** `VISUAL_LIVE_FUNCTIONAL_FREIGEGEBEN=1` nicht gesetzt — kein QEMU-Lauf, keine Operator-Ausgabe.

## Bereits belegt (statisch)

| Prüfung | Status |
|---------|--------|
| ISO SHA256 | match |
| Squashfs-Validator | Exit **0** |
| Bundle / Units / DE-Locale in Image | ja (offline) |

## Noch offen (nur in VM)

Login user/live, laufendes `/opt/setuphelfer-rescue`, aktiver Rescue-Backend, `/api/version` im Live-System.

## Operator — nächster Schritt

```bash
export VISUAL_LIVE_FUNCTIONAL_FREIGEGEBEN=1
cd /home/volker/piinstaller
ISO_PATH="build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"
qemu-system-x86_64 -m 2048 -smp 2 -cdrom "$ISO_PATH" -boot d -snapshot -no-reboot
```

Nach Login **user**/**live** die Checkliste aus `RESCUE_ISO_VISUAL_LIVE_SYSTEM_FUNCTIONAL_TEST_PLAN.md` ausführen und Ausgabe ingestieren.

**Rescue gesamt:** **yellow** (kein USB/Hardware/Restore).

JSON: `rescue_iso_visual_live_system_functional_validation_result_latest.json`
