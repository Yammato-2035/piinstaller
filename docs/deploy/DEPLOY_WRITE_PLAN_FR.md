> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_WRITE_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Write Plan (EN)

## Goal

Simulate a future Déploiement write flow to a target Périphérique without any real disk write.

## Properties

- simulation-only plan
- repeated safety gates
- code-based API responses
- every simulated operation has `auto_allowed=false`

## Hard blocks

- missing target / session mismatch
- system disk, live system
- Windows, dualboot
- Inconnu Périphérique
- Nonn-empty target
- invalid image inspect result

## Important Nonte

This phase performs Non writing, Partitioning, formatting, or image write.
