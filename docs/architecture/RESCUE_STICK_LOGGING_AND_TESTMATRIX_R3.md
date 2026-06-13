# Rettungsstick — Logging, Evidence und Testmatrix (R.3)

## Überblick

Kampagne R.3 stabilisiert Boot, Menü und Diagnose auf dem Setuphelfer-Rettungsstick. Alle Ergebnisse landen persistent unter:

```
/setuphelfer-evidence/
```

## Module

| Modul | Aufgabe |
|-------|---------|
| `rescue_persistence.py` | Stick-Erkennung, Evidence-Baum |
| `rescue_boot_logger.py` | Boot-/Menü-Kontext |
| `rescue_test_matrix.py` | 20-Bereiche-Ampelmatrix |
| `rescue_msi_diagnostics.py` | MSI Hardware read-only |
| `rescue_telemetry_spool.py` | Offline-Telemetrie |
| `rescue_evidence_bundle.py` | Gesamtpaket + nächste Aktionen |

## Sicherheitsprinzip

- **Interne Datenträger:** read-only, kein Schreib-Mount
- **Stick:** read-write nur für Evidence/Logs/Matrix/Telemetrie
- **Unsicherer Stick:** RAM unter `/tmp/setuphelfer-evidence/` + Warnung

## CLI auf dem Stick

```bash
setuphelfer-rescue-evidence.py detect|boot|matrix|bundle|menu-action
```

## Testmatrix

Dateien unter `matrix/` — Status `green|yellow|red|gray|blocked|unknown`.

## Nächste Phase (R.4)

- Browser/Display-Stack im Live-Image
- Telemetrie-Push ↔ Spool
- MSI-Boot-Verifikation auf Hardware

Siehe auch: `docs/architecture/RESCUE_STICK_PERSISTENCE_R3.md`, `docs/architecture/RESCUE_TEST_MATRIX_R3.md`.
