# RS-001 QEMU Menu Smoke

**Datum:** 2026-06-10  
**Status:** **not_run** (optional Level 5)

---

## Voraussetzungen

| Tool | Verfügbar |
|------|-----------|
| `qemu-system-x86_64` | prüfen mit `command -v` |
| Hybrid-ISO | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |

---

## Skript

```bash
./scripts/rescue-live/run-rs001-qemu-menu-smoke.sh
```

- Kein USB-Write
- Keine Zielplatte (`-snapshot`)
- Serial-Log unter `docs/evidence/runtime-results/rescue/rs001_qemu_menu_smoke_latest/`

---

## Regel

QEMU-Smoke ist **hilfreich, nicht zwingend** für Hardware-Freigabe. Level 1–4 müssen grün sein.
