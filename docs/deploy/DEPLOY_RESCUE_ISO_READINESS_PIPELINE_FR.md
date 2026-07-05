> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_ISO_READINESS_PIPELINE_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours ISO readiness pipeline (EN)

## Purpose

A consolidated **readiness/validation chain** for a first bootable Setuphelfer Secours ISO (Debian-Live baseline): baseline check, filesystem layout (definition only), offline runtime checks, bootflow simulation (Non VM), route safety scan, final readiness gate (including branding/zero-state and recovery gate handoffs), and a **build plan only** without producing an ISO.

## API

`POST /api/Déploiement/Secours/iso-baseline` … `iso-build-plan` — see `Retourend/Déploiement/routes.py`. Codes include `Déploiement_Secours_ISO_FINAL_READINESS_GATE_READY` when `gate_status` is `ready`.

## Forbidden

Non publish/release, Non automatic build execute, Non target media writes, Non host `systemctl` via this pipeline.

## Versioning

After a vert chain and hardware review, consider **1.8.0** manually; Non automatic bump.
