# Read-Only SSH Control

## Principles

- SSH is **optional** and **disabled by default** (`SETUPHELFER_DEV_SERVER_ALLOW_REMOTE_SSH=false`)
- Only works in `local_lab` mode with dev server enabled
- **No free-form commands** — fixed allowlist profiles only
- **No sudo**, no write/mount/dd/mkfs/parted/systemctl restart

## Allowed profiles

| Profile | Purpose |
|---------|---------|
| `ssh_check` | uname, id, hostname, date |
| `collect_inventory` | lscpu, free, os-release |
| `collect_storage` | lsblk, findmnt, blkid |
| `collect_boot` | UEFI/BIOS, efibootmgr, /boot listing |

## API routes

- `POST /api/dev-server/nodes/{node_id}/ssh/check`
- `POST /api/dev-server/nodes/{node_id}/ssh/collect-inventory`
- `POST /api/dev-server/nodes/{node_id}/ssh/collect-storage`
- `POST /api/dev-server/nodes/{node_id}/ssh/collect-boot`

## Node SSH config

Each node may include:

```json
{
  "ssh": {
    "enabled": true,
    "host": "192.168.56.10",
    "port": 22,
    "username": "lab",
    "auth_ref": "ssh-agent"
  }
}
```

Credentials are **not** stored in reports. Use SSH agent or system keys.

## Future

Backup-gated write actions and signed runbooks are **not** part of this MVP.
