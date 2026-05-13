# BR-001 — Read-only-Widerspruch (Shell vs. API) und `/api/version` 500

**Datum Erstanlage:** 2026-05-13 (Evidence-Nachzug; Inhalt bezieht sich auf Messungen **2026-05-13** am freigegebenen Pfad **`/media/gabriel/setuphelfer-back`**).

## Kontext

- Freigegebenes Ziel: **`/media/gabriel/setuphelfer-back`**, UUID **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`**, LABEL **setuphelfer-back**, FS **ext4**.
- **`/api/version`:** **HTTP 500** — siehe **`BR-001_backend_update_and_version_fix_2026-05-13.md`**: produktives **`/opt/setuphelfer/config/version.json`** hat **kein** `version_source_of_truth`-Schema; `core.versioning` validiert strikt und wirft.

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

## Verweise

- Gesamtlauf Deploy/Evidence: **`BR-001_backend_update_and_version_fix_2026-05-13.md`**
- Pfad-/Traverse-Historie: **`BR-001_productive_target_check_media_path_analysis_2026-05-12.md`**
