> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_WRITE_TEST_HARNESS_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Write Test Harness (EN)

## Goal

Isolated test harness for future real-write phases, with write logic allowed only for approved test files.

## Safety frame

- Nee blockApparaats
- Nee /dev/* targets
- Nee mount/loop/format/Partitie
- regular files only under allowed test prefixes
- hard max_bytes limit

## API

- `POST /api/Deploy/write/harness/session`
- `POST /api/Deploy/write/harness/execute`
