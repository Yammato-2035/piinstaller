# FAQ – Rescue / Rettungsstick (Deutsch)

> Vollständige FAQ inkl. älterer Phasen: `docs/faq/RESCUE_FAQ.md`  
> R.3 Architektur: `docs/architecture/RESCUE_STICK_LOGGING_AND_TESTMATRIX_R3.md`

## Wo liegen Logs und die Testmatrix auf dem Stick?

Unter **`/setuphelfer-evidence/`**:

| Pfad | Inhalt |
|------|--------|
| `boot/` | Kernel, UEFI, cmdline |
| `menu/` | TUI-Menü-Ergebnisse |
| `hardware/msi_diagnostics_latest.md` | MSI-Read-only-Diagnose |
| `matrix/rescue_test_matrix_latest.md` | Ampel-Matrix (20 Bereiche) |
| `summaries/rescue_evidence_latest.md` | Gesamt-Bundle |

## Was bedeuten die Matrix-Status?

`green` = ok · `yellow` = eingeschränkt · `red` = Fehler · `gray` = nicht anwendbar · `blocked` = absichtlich gesperrt · `unknown` = nicht bewertet

## Schreibt der Stick auf interne Festplatten?

**Nein.** Nur der erkannte Setuphelfer-Rettungsstick (oder RAM-Fallback mit Warnung).

## Warum kein grafisches Menü / Browser?

Das aktuelle Live-Image enthält **keinen Browser** und keinen vollständigen Display-Stack (siehe `docs/evidence/rescue/GRAPHICAL_BOOT_AND_KIOSK_AUDIT_R3.md`). TUI-Fallback ist aktiv.

## Wie starte ich die Evidence-Erzeugung manuell?

```bash
setuphelfer-rescue-evidence.py bundle
```
