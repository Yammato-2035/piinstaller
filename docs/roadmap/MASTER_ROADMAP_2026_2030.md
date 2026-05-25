# Setuphelfer Master Roadmap 2026-2030

## Zweck

Diese Master-Roadmap ist die langfristige Uebersicht fuer Produkt-, Runtime- und Safety-Arbeit.
Die operative Ampelbewertung bleibt in `docs/roadmap/STATUS_MATRIX.md`.

## Leitplanken

- Keine Schoenfaerbung von Release-Gates
- Safety-Gates bleiben vor Komfortfunktionen
- Read-only Cockpit-/Dashboard-Evidence geht vor manuellen Bauchgefuehlen
- Runtime unter `/opt/setuphelfer` und Workspace muessen nachvollziehbar auseinandergehalten werden

## Horizonte

### 2026

- Development Dashboard als belastbare Read-only Steuerzentrale
- kontrollierter Deploy-Helper, Update-Status und Rescue-ISO-Prebuild reproduzierbar
- Backup/Restore/Live-Boot weiter nur mit echter Hardware-Evidence

### 2027

- Monolith-Grenzen explizit dokumentieren und schrittweise entkoppeln
- Packaging-Readiness von Installationsabnahme trennen
- Testregister und Evidence-Index als dauerhafte Governance-Artefakte pflegen

### 2028-2030

- Release-Gates, Packaging und Diagnostics weiter konsolidieren
- Cloud-/Edition-Themen nur nach stabiler Runtime- und Hardware-Basis

## Verweise

- `docs/roadmap/STATUS_MATRIX.md`
- `docs/architecture/MONOLITH_BOUNDARY_MAP.md`
- `docs/evidence/TEST_FAILURE_REGISTER.md`
- `docs/evidence/EVIDENCE_INDEX.md`
