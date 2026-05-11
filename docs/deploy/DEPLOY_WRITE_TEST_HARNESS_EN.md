# Deploy Write Test Harness (EN)

## Goal

Isolated test harness for future real-write phases, with write logic allowed only for approved test files.

## Safety frame

- no blockdevices
- no /dev/* targets
- no mount/loop/format/partition
- regular files only under allowed test prefixes
- hard max_bytes limit

## API

- `POST /api/deploy/write/harness/session`
- `POST /api/deploy/write/harness/execute`
