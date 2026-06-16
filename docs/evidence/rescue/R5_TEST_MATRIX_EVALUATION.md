# R.5 — Testmatrix-Auswertung

## Status

**Ausstehend** — `rescue_test_matrix_latest.md` vom Stick nicht verfügbar (kein MSI-Boot).

## Vorläufige Workspace-Matrix (statisch R.4)

Aus `build_r4_static_matrix_entries()` im Repo:

| Bereich | Status | Evidence | Blocker | Nächste Aktion |
|---------|--------|----------|---------|----------------|
| Boot | gray | — | kein HW-Boot | MSI-Boot |
| GRUB | yellow | R5_GRUB_PREFLIGHT | grub.cfg fehlt pre-build | lb build |
| Stick-Persistenz | gray | — | kein Stick-Boot | MSI-Boot |
| TUI | gray | — | — | MSI-Boot |
| Grafisches Menü | yellow | Staging OK | ISO stale | Neuer Build |
| Browser | green (pkg) / red (ISO) | R5_SQUASHFS | stale ISO | Gate A Build |
| Kiosk | green (scripts) / red (ISO) | R5_SQUASHFS | stale ISO | Gate A Build |
| React UI | gray | — | nicht im stale ISO | Build + UI bundle |
| WLAN | gray | — | — | MSI-Boot |
| Netzwerk | gray | — | — | MSI-Boot |
| Telemetrie-Spool | green (code) / red (ISO) | R4 integration | stale ISO | Build |
| Telemetrie-Ingest | gray | — | — | Netzwerk + Boot |
| MSI-Hardware | gray | — | — | MSI-Boot |
| Interne RO | green (policy) | code | — | — |
| Backup-Ziel | gray | — | — | BR-001 später |
| Restore-Gate | blocked | policy | by design | — |
| Partitions RO | green | policy | — | — |
| Logs/Evidence | gray | — | kein Stick | MSI-Boot |
| Nächste Aktion | yellow | — | Gate A | ISO bauen |

## Nach MSI-Boot

Stick-Datei `matrix/rescue_test_matrix_latest.md` hier eintragen und Ampeln aktualisieren.
