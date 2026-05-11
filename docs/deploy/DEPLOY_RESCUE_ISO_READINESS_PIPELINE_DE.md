# Deploy — Rescue ISO Readiness Pipeline (DE)

## Zweck

Konsolidierte **Readiness-/Validierungskette** für eine erste bootfähige Setuphelfer-Rescue-ISO (Debian-Live-Basis): Baseline-Check, Dateisystem-Layout (nur Definition), Offline-Runtime-Prüfung, Bootflow-Simulation (ohne VM), Safety-Scan der Routen, finales Readiness-Gate (inkl. Branding/Zero-State und Recovery-Gate-Handoffs) sowie ein reiner **Build-Plan** ohne ISO-Erzeugung.

## API

`POST /api/deploy/rescue/iso-baseline` … `iso-build-plan` — siehe `backend/deploy/routes.py`. Codes `DEPLOY_RESCUE_ISO_BASELINE_*`, …, `DEPLOY_RESCUE_ISO_FINAL_READINESS_GATE_READY` bei `gate_status: ready`.

## Verbote

Kein Publish/Release, kein automatischer Build-Execute, keine Schreibzugriffe auf Zielmedien, kein `systemctl` am Host durch diese Pipeline.

## Version

Nach grüner Kette und Hardware-Sichtung manuell **1.8.0** erwägen; kein automatischer Bump.
