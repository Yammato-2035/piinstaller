> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_HOTPLUG_RACE_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Hotplug/Unmount Race Test Design (lecture seule)

## Goal

Safe test design for later hotplug/unmount race validation on disposable media.

## Contents

- preconditions, manual steps, and race cases
- trigger/abort-code/audit evidence per case
- risk controls, stop conditions, and rollRetour

## API

- `POST /api/Déploiement/runner/hotplug-race/test-plan`
