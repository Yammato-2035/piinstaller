# R.7 — SquashFS Runtime Validation

**Datum:** 2026-06-10  
**Quelle:** `/media/gabriel/SETUPHELFER/live/filesystem.squashfs` (Stick vom Write `fat32_esp_write_20260613_171403`)  
**ISO SHA256:** `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143`

## Pflichtprüfung

| Artefakt | Status | Hinweis |
|----------|--------|---------|
| chromium | **FOUND** | 78 Treffer in unsquashfs -ll |
| openbox | **FOUND** | 211 Treffer |
| xinit | **FOUND** | 15 Treffer |
| `setuphelfer-rescue-evidence.py` | **FOUND** | `usr/local/sbin/` |
| `setuphelfer-rescue-telemetry-push` | **FOUND** | `usr/local/sbin/` |
| `setuphelfer-rescue-boot-evidence-init` | **MISSING** | 0 Treffer |
| `rescue_persistence.py` v4 + boot_marker | **MISSING** | v3, kein `initialize_boot_evidence_marker` |
| `evidence.py boot-init` | **MISSING** | kein Subcommand im Squashfs |
| `start-assistant` boot-hook | **MISSING** | kein `boot-evidence-init` Aufruf |
| `rescue.html` | **FOUND** | `usr/share/setuphelfer/rescue/ui/` |
| Matrix v4 | **FOUND** | `RESCUE_TEST_MATRIX_VERSION = 4` |
| R6 boot_marker Support | **MISSING** | `initialize_boot_evidence_marker: 0` |

## Validator-Skript

```bash
./scripts/rescue-live/validate-rescue-iso-squashfs.sh binary.hybrid.iso
```

Exit **0** — prüft Basis-Bundle, **nicht** R.6-spezifische Artefakte.

## Entscheidung

**blocked_runtime**

Begründung: Squashfs auf Stick enthält **keinen** R.6 Boot-Persistence-Hook. USB-Write mit diesem ISO kann `boot_marker` auf Hardware nicht erzeugen.

**Nicht** `ready_for_usb_write` (für R.7-Ziel).
