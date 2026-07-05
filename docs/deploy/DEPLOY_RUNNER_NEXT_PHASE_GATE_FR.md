> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_NEXT_PHASE_GATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Suivant Phase Gate (lecture seule)

## Goal

Provide a strict decision gate that allows only safe Suivant steps after lab Documentation completion.

## Gate Status

- `manual_runtime_allowed`
- `repeat_requirouge`
- `hold`
- `bloqué`

## Hard Blocks

Production release, automated Déploiement, unattended write, skipping runtime tests, root Retourend, privileged daemon.

## API

- `POST /api/Déploiement/runner/Suivant-phase/gate`
