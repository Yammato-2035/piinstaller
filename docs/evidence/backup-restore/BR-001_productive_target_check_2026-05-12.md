# BR-001 — Produktiver target-check / Deploy-Versuch (2026-05-12)

## Phase 1 — Ist-Zustand

| Prüfung | Ergebnis |
|--------|----------|
| Workspace `pwd` | `/home/volker/piinstaller` |
| `git rev-parse HEAD` | `b77c109d402a053cec4544a06919613b9167624d` |
| Produktiver Backend-Pfad | `/opt/setuphelfer/backend` (kein `.git`; Dateien `setuphelfer:setuphelfer`, Gruppe schreibbar für Deploy) |
| `systemd` | `User=setuphelfer`, `Group=setuphelfer`, `WorkingDirectory=/opt/setuphelfer`, `ExecStart=/opt/setuphelfer/scripts/start-backend.sh` |
| `GET /api/version` | `success`, `1.5.0.0`, `install_profile: opt` |

### Gerät / Mount (Abweichung zur Freigabe **nur /dev/sdd1**)

`lsblk -f` (Auszug):

- **`setuphelfer-back`** (ext4, gleiche UUID wie zuvor dokumentiert) hängt aktuell an **`/dev/sda1`** → `/media/gabriel/setuphelfer-back`
- **`/dev/sdd1`** ist jetzt **INTENSO** (exfat) unter `/media/gabriel/INTENSO` — **nicht** mehr das unter Freigabe genannte ext4-Volume.

`stat`:

- **`/mnt/setuphelfer/backups`:** Gerät **259/9** (Zuordnung zu Root-/nvme-Stack, nicht `8/x` externes USB-Layout wie `/media/.../setuphelfer-backups` mit Gerät **8/1**).

`findmnt -T /mnt/setuphelfer/backups` (als `gabriel`):

- liefert nur **`/`** / **`/dev/nvme0n1p2`** — kein sichtbarer Bind auf externes Volume.

**Fazit Phase 1:** Die Freigabe „**ausschließlich /dev/sdd1** … setuphelfer-back“ ist mit dem **aktuellen** Host-Layout **nicht erfüllbar** (Label auf **sda1**, sdd1 = INTENSO). **→ Deploy nach Freigabe-Logik gestoppt / nachversucht rollback.**

## Phase 2 — Diff Workspace vs. /opt (vor Rollback)

Nach Kopie waren `app.py` und `safe_device.py` SHA256-identisch zum Workspace; `diff` war leer. Vorherige Produktivstände (SHA256 aus Backup):

- `app.py`: `68a740b7…`
- `safe_device.py`: `2c0085c5…`

## Phase 3 — Deploy / Rollback

1. Backup unter **`/tmp/setuphelfer-deploy-backup-20260512T194722Z/`** (Kopien von `app.py`, `safe_device.py` + `sha256sum` dokumentiert).
2. Kurzzeitig Workspace-Dateien nach `/opt/setuphelfer/backend/` kopiert (`cp` ohne vollständiges `-a` wegen Timestamps).
3. Nach Erkennen der **Geräte-Freigabe-Abweichung:** **Rollback** auf die Backup-Kopien (SHA256 wieder wie oben).

**Tests** wurden **nicht** nach `/opt` kopiert.

## Phase 4 — Restart

`sudo -n systemctl restart setuphelfer-backend.service` → **Passwort nötig**, nicht ausgeführt.

## Phase 5 — Dienstnutzer

`sudo -n -u setuphelfer test …` → **nicht ausgeführt** (Passwort).

## Phase 6 — Produktiver `target-check`

**Request:** `GET http://127.0.0.1:8000/api/backup/target-check?backup_dir=/mnt/setuphelfer/backups&create=0`

**Response (vollständig, nach Rollback — gleicher Fehler wie bei kurzzeitig aktualisierten Dateien):**

```json
{
  "status": "error",
  "message": "Ungültiges Backup-Ziel: STORAGE-PROTECTION-004: Mount-Quelle ist kein einfaches Blockgerät (z. B. mapper) [mount_source_seen=/dev/nvme0n1p2[/mnt]; resolved_source=(none); fstype=ext4; target=/mnt; reason=no_resolvable_block_source]",
  "code": "backup.path_invalid",
  "severity": "error",
  "details": {
    "reason": "STORAGE-PROTECTION-004: Mount-Quelle ist kein einfaches Blockgerät (z. B. mapper) [mount_source_seen=/dev/nvme0n1p2[/mnt]; resolved_source=(none); fstype=ext4; target=/mnt; reason=no_resolvable_block_source]"
  }
}
```

**Interpretation:** Pfad fällt für `findmnt -T` unter den **internen** `/`-/`/mnt`-Baum (`nvme0n1p2[/mnt]`); ohne produktive Bind-Mount-Kette auf das **freigegebene** externe Volume ist das Ziel **nicht** BR-001-tauglich — **kein** `target_check_ok`.

## Phase 7 — BR-001

**blocked** — kein Backup gestartet.

## Abnahme (Vorgabe)

| Kriterium | Erfüllt? |
|-----------|----------|
| Produktiver Dienst nutzt aktuellen Fix | **Nein** (Rollback; zudem kein Restart) |
| target-check grün | **Nein** |
| Kein Backup | **Ja** |
| Safety nicht abgeschwächt | **Ja** |
