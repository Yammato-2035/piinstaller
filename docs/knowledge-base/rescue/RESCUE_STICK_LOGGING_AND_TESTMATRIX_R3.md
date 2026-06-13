# Rettungsstick — Logging & Testmatrix (Kurzüberblick R.3)

Der Rettungsstick schreibt ab Boot automatisch Diagnose-Ergebnisse nach `/setuphelfer-evidence/` auf dem Stick (oder ins RAM mit Warnung).

**Wichtig:** Interne Festplatten werden nicht beschrieben.

## Was finde ich auf dem Stick?

| Ordner | Inhalt |
|--------|--------|
| `boot/` | Kernel, UEFI, cmdline, Live-Umgebung |
| `menu/` | TUI-Menüaktionen |
| `hardware/` | MSI-Diagnose |
| `matrix/` | Testmatrix JSON/MD |
| `telemetry/spool/` | Offline-Telemetrie |
| `summaries/` | Gesamt-Bundle |

## Testmatrix lesen

`matrix/rescue_test_matrix_latest.md` — Ampeln und `next_action` pro Bereich.

## Assistent

`setuphelfer-rescue-start-assistant` — fängt Fehler ab, kehrt ins Menü zurück, blockiert Schreibaktionen.

Ausführlich: `docs/architecture/RESCUE_STICK_LOGGING_AND_TESTMATRIX_R3.md`
