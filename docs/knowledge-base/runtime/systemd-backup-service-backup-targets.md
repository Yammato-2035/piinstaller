# systemd und Backup-Ziele (Setuphelfer Backend)

## Kurzüberblick

| Option | Rolle |
|--------|--------|
| `User=` / `Group=` | Dienst läuft als **`setuphelfer`** (kein `User=root` für das API-Backend). |
| `SupplementaryGroups=setuphelfer` | Tar/Dateizugriff auf team-sichtbare Verzeichnisse mit Gruppe **`setuphelfer`**. |
| `ProtectSystem=strict` | Schreiben nur unter **`ReadWritePaths`** und wenigen weiteren Ausnahmen. |
| `ProtectHome=yes` | Kein Zugriff auf fremde **`/home/*`**-Inhalte — daher sind **Login-only**-Mounts unter `/media/<user>/` besonders problematisch. |
| `PrivateTmp=yes` | Temporäre Dateien nur im isolierten Service-`/tmp`. |
| `NoNewPrivileges=true` | Kein suid/sudo-Eskalationspfad aus dem Dienst. |

## ReadWritePaths

Die ausgelieferte Unit enthält u. a.:

- `{{INSTALL_DIR}}` bzw. `/opt/setuphelfer`
- `/etc/setuphelfer`, `/var/log/setuphelfer`, `/var/lib/setuphelfer`
- `/tmp`, `/mnt`, `/mnt/setuphelfer`
- **`/media/setuphelfer`** — stabiler Operator-Baum für **externe** USB-Ziele ohne Abhängigkeit von einem konkreten Desktop-Login.

Zusätzliche Pfade nur per **Drop-in** (`*.conf` unter `setuphelfer-backend.service.d/`), nicht durch Abschwächung der Sandbox.

## Verwandte Dokumentation

- `docs/knowledge-base/storage/external-backup-target-architecture.md`
- `docs/operations/systemd/setuphelfer-backend-backup-target.conf.example`
- `packaging/systemd/setuphelfer-backup@.service`
