# Backup Decomposition Plan — B.1

## Größte Monolithen (Backup-Domain)

1. `POST /api/backup/create` — async jobs, sudo, tar
2. `POST /api/backup/restore` — sandbox/preview coupling
3. `GET/POST /api/backup/clone/*` — storage discovery + write risk
4. `POST /api/backup/usb/*` — mount/prepare/eject

## Empfohlene Reihenfolge

1. B.2 Readonly router (`status`, `settings`, `list`, `jobs`, `profiles` GET)
2. B.3 Target discovery facade (delegiert `storage_discovery`)
3. B.4 Preview/verify plan-only
4. B.5 Execute isolation (eigener Orchestrator, Risk-Gate)

Keine Extraktion in B.1.
