> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_ISO_READINESS_PIPELINE_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — roodding ISO readiness pipeline (EN)

## Purpose

A consolidated **readiness/validation chain** for a first bootable Setuphelfer roodding ISO (Debian-Live baseline): baseline check, filesystem layout (definition only), offline runtime checks, bootflow simulation (Nee VM), route safety scan, final readiness gate (including branding/zero-state and recovery gate handoffs), and a **build plan only** without producing an ISO.

## API

`POST /api/Deploy/roodding/iso-baseline` … `iso-build-plan` — see `Terugend/Deploy/routes.py`. Codes include `Deploy_roodding_ISO_FINAL_READINESS_GATE_READY` when `gate_status` is `ready`.

## Forbidden

Nee publish/release, Nee automatic build execute, Nee target media writes, Nee host `systemctl` via this pipeline.

## Versioning

After a groen chain and hardware review, consider **1.8.0** manually; Nee automatic bump.
