# BR-001 — Read-only-Widerspruch (Shell vs. API) und `/api/version` 500

**Datum Erstanlage:** 2026-05-13 (Evidence-Nachzug; Inhalt bezieht sich auf Messungen **2026-05-13** am freigegebenen Pfad **`/media/gabriel/setuphelfer-back`**).

## Root cause (2026-05-13): systemd `ProtectSystem=strict` / `ReadWritePaths`

Der Widerspruch **Shell `rw`** vs. **API EROFS** ist mit hoher Wahrscheinlichkeit der **systemd-Service-Sandbox** geschuldet: **`/media/gabriel/setuphelfer-back`** fehlte in **`ReadWritePaths`**, während **`ProtectSystem=strict`** aktiv war — Schreibzugriffe unter **`/media/...`** werden im Namespace **verweigert** (EROFS), unabhängig vom echten Mount-**`rw`** auf dem Host.  
**Nachweis und Operator-Schritte:** **`BR-001_systemd_readwritepaths_analysis_2026-05-13.md`**; Repo-Fix in **`debian/setuphelfer-backend.service`** / **`setuphelfer-backend.service`**; Drop-in-Beispiel **`docs/operations/systemd/setuphelfer-backend-backup-target.conf.example`**.

## Kontext

- Freigegebenes Ziel: **`/media/gabriel/setuphelfer-back`**, UUID **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`**, LABEL **setuphelfer-back**, FS **ext4**.
- **`/api/version`:** (historisch) **HTTP 500** bei Legacy-`config/version.json` — siehe **`BR-001_backend_update_and_version_fix_2026-05-13.md`**. Nach Update kann die API auch **nur** `project_version` / `release_stage` / `version_track` liefern (**ohne** `status`); das **Version-Gate-Skript** akzeptiert dieses schlanke Format (**2026-05-13**).

## Beobachtung A — Shell (`findmnt`)

```text
findmnt -T /media/gabriel/setuphelfer-back -o TARGET,SOURCE,FSTYPE,OPTIONS
→ OPTIONS: rw,nosuid,nodev,relatime,...
```

`mount` / `/proc/mounts` zeigen für dieselbe Zeile ebenfalls **`rw`**.

## Beobachtung B — API `target-check`

**Request:** `GET /api/backup/target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0`

Auszug aus der JSON-Antwort:

- **`mount.options`:** **`ro,nosuid,nodev,…`**
- **`mount.mount_readonly`:** **`true`**
- **`write_test.success`:** **`false`**
- **`write_test.reason_code`:** **`mount_readonly`**
- Detail: **`[Errno 30] Read-only file system`** auf temporärer Schreibprobe unter dem Zielpfad
- **`code`:** **`backup.backup_target_not_writable`**

## Widerspruch

| Quelle | `rw`/`ro` für dasselbe Mount |
|--------|------------------------------|
| Shell `findmnt` / `mount` | **rw** |
| Backend-Antwort | **ro** + EROFS |

## Mögliche Ursachenklassen (nur Analyse, keine Reparatur in diesem Ticket)

1. **Race / Zustandswechsel:** Mount zwischen Shell-Messung und API-Aufruf von `rw` auf `ro` gewechselt (z. B. Policy, udisks, manuelle Aktion) — hier nicht belegt, nur als Kategorie.
2. **Unterschiedliche Sicht:** API wertet Mount-Informationen aus einer anderen Quelle oder nach zusätzlicher Normalisierung als die Shell-Zeile (z. B. erneuter `findmnt`-Pfad, gecachte Daten, oder abweichender Parser).
3. **Prozesskontext:** Dienst läuft als **`setuphelfer`**; Schreibtest im Prozess schlägt mit EROFS fehl, während interaktive Shell als anderer User andere effektive Rechte/Namespaces sieht (selten, aber dokumentierbar als Hypothese).
4. **NS/Mount-Namespace:** Unwahrscheinlich bei typischem systemd, aber als generische Kategorie erwähnbar.

## Abgrenzung

- **Kein** `remount,rw`, **keine** automatische Reparatur, **kein** Backup-Start.
- Kein alternativer Backup-Pfad.

## Messung 2026-05-13 (zeitgleich Gate-Skript-Fix, nur Analyse)

**Zeitstempel Start/Ende:** `2026-05-13T18:03:33+02:00` (lokal).

### `findmnt -T /media/gabriel/setuphelfer-back`

```text
TARGET                          SOURCE    FSTYPE OPTIONS
/media/gabriel/setuphelfer-back /dev/sdb1 ext4   rw,nosuid,nodev,relatime,errors=remount-ro,stripe=8191
```

### `/proc/mounts` (Auszug)

```text
/dev/sdb1 /media/gabriel/setuphelfer-back ext4 rw,nosuid,nodev,relatime,errors=remount-ro,stripe=8191 0 0
```

### `lsblk` (relevant)

- **`/dev/sdb1`:** ext4, LABEL **setuphelfer-back**, UUID **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`**, MOUNTPOINT **`/media/gabriel/setuphelfer-back`**, **RO**-Spalte **0**, TRAN **usb**.

### `target-check` (gleicher Zeitpunkt)

**Request:** `GET /api/backup/target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0`

- **`mount.options`:** **`ro,...`**, **`mount_readonly": true`**
- **`write_test`:** EROFS, **`reason_code":"mount_readonly"`**
- **`code`:** **`backup.backup_target_not_writable`**

### Fazit Messung

**Widerspruch bleibt:** Shell-**`rw`** vs. API-**`ro`** + EROFS auf Schreibprobe — **keine** Reparatur, **kein** `remount,rw`, **kein** Backup.
