# Automatische Vorbereitung externer Backup-Ziele

## Warum legt Setuphelfer ein eigenes Verzeichnis auf dem externen Datenträger an?

Der Dienst **`setuphelfer-backend`** läuft als Benutzer **`setuphelfer`**, nicht als Ihr Desktop-Login. udisks mountet USB oft unter **`/media/<login>/…`** mit **0700** — der Dienst kann dort nicht zuverlässig schreiben.

Setuphelfer nutzt deshalb einen **eigenen, stabilen Baum**:

`/media/setuphelfer/<label>`

Dort werden nur **eigene** Mounts/Bind-Mounts und Rechte **`root:setuphelfer`** (0770) angelegt. **Keine** fremden Dateien werden gelöscht oder überschrieben.

## API (Operator / UI)

### Kandidaten anzeigen (read-only)

```bash
curl -s http://127.0.0.1:8000/api/backup/external-targets | jq .
```

### Ziel automatisch vorbereiten (sudo-Passwort erforderlich)

```bash
curl -s -X POST http://127.0.0.1:8000/api/backup/target-prepare \
  -H 'Content-Type: application/json' \
  -d '{"label":"br001","mode":"auto","sudo_password":"***"}' | jq .
```

Erfolg: **`diagnosis_id`: `BACKUP-TARGET-AUTO-MOUNT-READY`**, **`backup_dir`**: `/media/setuphelfer/br001`.

### target-check mit Auto-Vorbereitung

```bash
curl -sG 'http://127.0.0.1:8000/api/backup/target-check' \
  --data-urlencode 'backup_dir=/media/setuphelfer/br001' \
  --data-urlencode 'auto_prepare=1' \
  --data-urlencode 'label=br001' | jq .
```

(`auto_prepare=1` nur wenn Sudo-Passwort im Backend gespeichert ist.)

## Modi

| mode | Verhalten |
|------|-----------|
| `auto` | Bind-Mount von bestehendem udisks-Mount (`/media/<user>/…`) wenn vorhanden, sonst Direkt-Mount per UUID |
| `bind` | Erzwingt Bind-Mount |
| `direct` | Mount `UUID=…` direkt auf `/media/setuphelfer/<label>` |

## Diagnose-IDs

| ID | Bedeutung |
|----|-----------|
| `BACKUP-TARGET-AUTO-MOUNT-READY` | Ziel vorbereitet und validiert |
| `BACKUP-TARGET-AUTO-MOUNT-FAILED` | Vorbereitung fehlgeschlagen (Details in `details.step`) |
| `STORAGE-PROTECTION-007` | Ziel noch nicht gemountet (vor Vorbereitung) |

## Was blockiert bleibt

- Interne NVMe/Systemplatte als Backup-Ziel
- `/media/<login>/…` direkt als `backup_dir`
- `chmod 777`, Formatieren, Löschen fremder Daten

## FAQ

**Warum legt Setuphelfer ein eigenes Verzeichnis auf dem externen Datenträger an?**

Weil der Dienst als **`setuphelfer`** läuft, nicht als Ihr Desktop-Login. udisks mountet oft unter **`/media/<Benutzer>/…`** mit Rechten nur für diesen Benutzer. Unter **`/media/setuphelfer/<label>`** sind Bind-Mount oder Direkt-Mount und **`root:setuphelfer`** (0770) stabil und prüfbar — ohne fremde Daten zu löschen.

**Warum ist `/media/<user>` problematisch?**

Typisch **0700** für den Session-User; der Backend-Dienst hat dort kein zuverlässiges Schreibrecht.

**Warum keine internen Ziele?**

`STORAGE-PROTECTION-*` blockiert Systemplatten und Root-FS — Backups sollen auf echte externe Medien.

## Runtime-Deploy (Operator)

1. Backend nach `/opt` synchronisieren (z. B. `rsync` aus dem Repo oder `sudo ./scripts/deploy-to-opt.sh`).
2. `systemctl restart setuphelfer-backend.service`
3. Mount: `sudo ./scripts/operator/setup-external-backup-target.sh br001`  
   (ohne interaktives sudo-TTY alternativ: `systemd-run --wait -p User=root bash …/setup-external-backup-target.sh br001`)
4. `curl -sG 'http://127.0.0.1:8000/api/backup/target-check' --data-urlencode 'backup_dir=/media/setuphelfer/br001'`

## Siehe auch

- `external-backup-target-mount.md`
- `external-backup-target-architecture.md`
- `scripts/operator/setup-external-backup-target.sh` (Shell-Alternative)
