# Debian Live – Basisentscheidung (Entwurf)

**Status:** Gelb – technische Vorarbeit im Repo (Deploy-/Rescue-Runner), **kein** abgenommener Produktions-ISO-Build in dieser Session.

## Optionen

| Option | Vorteil | Nachteil |
|--------|---------|----------|
| Debian Live offiziell | breite HW-Unterstützung, reproduzierbare Basis | Build-Pipeline pflegen |
| Andere Live-Distribution | spezifische Treiber | abweichende Toolchain |

## Arbeitsannahme

- **Debian Live** als Referenzbasis für Rescue-Stick, solange nicht durch Evidence widerlegt.

## Nächste Schritte

1. Build-Emulation / Sandbox laut `docs/evidence/rescue-stick/build_emulation.json` ausführen.  
2. Read-only-Anforderungen in `read_only_requirements.json` konkretisieren.  
3. Ersten echten Boot erst nach Freigabe-Runbook (kein automatischer Restore).
