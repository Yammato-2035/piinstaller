> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_WRITE_TEST_HARNESS_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Write Test Harness (EN)

## Goal

Isolated test harness for future real-write phases, with write logic allowed only for approved test files.

## Safety frame

- Non blockPériphériques
- Non /dev/* targets
- Non mount/loop/format/Partition
- regular files only under allowed test prefixes
- hard max_bytes limit

## API

- `POST /api/Déploiement/write/harness/session`
- `POST /api/Déploiement/write/harness/execute`
