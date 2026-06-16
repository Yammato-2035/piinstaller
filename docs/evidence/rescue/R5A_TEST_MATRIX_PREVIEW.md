# R.5A — Testmatrix (vorläufig)

**Quelle:** Workspace `build_r4_static_matrix_entries()` + stale SquashFS

| ID / Bereich | Ampel | Grund |
|--------------|-------|-------|
| R4-BROWSER-PKG-001 | green (config) / **red** (ISO) | Package-Liste OK, SquashFS fehlt |
| R4-DISPLAY-PKG-001 | green (config) / **red** (ISO) | dito |
| R4-KIOSK-001 | green (scripts) / **red** (ISO) | dito |
| R4-GRUB-THEME-001 | **yellow** | Staging OK, grub.cfg pending |
| R4-TELEM-SPOOL-INT-001 | **green** (Repo) | Push-Skript integriert |
| R3-PERSIST-001 | **gray** | kein Stick-Boot |

## Nach neuem Build + SquashFS-Check

Alle R.4-Pfade FOUND → Einträge auf **green** setzen in `R5A_FINAL_RESULT.md`.
