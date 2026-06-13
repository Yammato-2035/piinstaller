# R.3 — Boot Logger Evidence

**Modul:** `backend/core/rescue_boot_logger.py`  
**Ziel-Pfad:** `setuphelfer-evidence/boot/`  
**Tests:** `backend/tests/test_rescue_boot_logger_r3.py` (2 Tests, OK)

## Erfasste Kontexte

| Funktion | Inhalt |
|----------|--------|
| `collect_boot_context()` | Zeit, Hostname, Kernel, Live-Flags |
| `collect_bootloader_context()` | UEFI/BIOS, Secure-Boot-Indizien |
| `collect_kernel_cmdline()` | `/proc/cmdline`, Setuphelfer-Flags |
| `collect_live_environment()` | Live-Medium, Stick-Mount |
| `collect_menu_context()` | TUI/grafisch, Display, Browser, X/Wayland |
| `write_boot_evidence_bundle()` | JSON + Text nach `boot/` |

## Journal

`_collect_journal_snippets()` — nur lesend, begrenzte Zeilen, Fehler werden ignoriert (kein Risiko für Host).

## Integration

- `setuphelfer-rescue-evidence.py boot`
- Evidence-Bundle (`rescue_evidence_bundle.py`) ruft Boot-Bundle beim Gesamtpaket auf

## Fallback

Wenn Stick nicht sicher beschreibbar: `/tmp/setuphelfer-evidence/boot/` mit Warnung in Metadaten.
