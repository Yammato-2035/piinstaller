# Deploy — Rescue ISO readiness pipeline (EN)

## Purpose

A consolidated **readiness/validation chain** for a first bootable Setuphelfer rescue ISO (Debian-Live baseline): baseline check, filesystem layout (definition only), offline runtime checks, bootflow simulation (no VM), route safety scan, final readiness gate (including branding/zero-state and recovery gate handoffs), and a **build plan only** without producing an ISO.

## API

`POST /api/deploy/rescue/iso-baseline` … `iso-build-plan` — see `backend/deploy/routes.py`. Codes include `DEPLOY_RESCUE_ISO_FINAL_READINESS_GATE_READY` when `gate_status` is `ready`.

## Forbidden

No publish/release, no automatic build execute, no target media writes, no host `systemctl` via this pipeline.

## Versioning

After a green chain and hardware review, consider **1.8.0** manually; no automatic bump.
