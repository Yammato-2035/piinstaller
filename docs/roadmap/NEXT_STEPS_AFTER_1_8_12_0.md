# Next Steps after 1.8.12.0

**Stand:** 2026-06-16 → **1.9.0.0** (Commercial Boundary + MSI Plan)

## Abgeschlossen (1.8.12.0)

- System-Router E.13 (20 Routen)
- Security-Router E.14 (8 Routen)
- Deploy `/opt/setuphelfer` @ 1.8.12.0

## Abgeschlossen (1.9.0.0 — dieser Lauf)

- Commercial/Public Boundary dokumentiert und Gate verschärft
- MSI Windows→Linux Teststrang als Plan/Runbooks/Evidence-Schema
- Blueprint-Begriffe und public/private Split
- Monolith-Audit vor weiterer Produktarbeit

## Priorität (nicht verhandelbar)

1. **Commercial/Public Boundary** — vor jedem Commit Gate
2. **MSI Windows Backup/Restore Plan** — Dokumentation ✅; Runtime separat
3. **MSI Linux Blueprint Plan** — Dokumentation ✅
4. Operator-Freigabe → **MSI Read-only Precheck** (nächster Prompt)
5. Separater Lauf: MSI Backup
6. Separater Lauf: Restore-Test
7. Separater Lauf: Linux-Installation + Blueprint

## Explizit nicht als Nächstes

- Cloud Edition Free/Pro Implementierung
- Telemetrie-/Diagnostikserver im Public Repo
- Operator-Dashboard Implementierung
- Monolith E.15 (users) vor MSI-Precheck-Freigabe optional

## Nächster Prompt

```
STRICT MODE – MSI WINDOWS READ-ONLY PRECHECK RUNTIME
```
