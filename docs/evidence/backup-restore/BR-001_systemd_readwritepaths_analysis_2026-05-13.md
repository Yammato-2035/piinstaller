# BR-001 — systemd `ReadWritePaths` und rw/ro-Widerspruch (2026-05-13)

**Modus:** STRICT — nur Analyse und Repo-Anpassung; **kein** Backup, **kein** Restore, **kein** remount, **kein** anderer Zielpfad als **`/media/gabriel/setuphelfer-back`**.

## Freigabe

| Feld | Wert |
|------|------|
| Zielpfad | **`/media/gabriel/setuphelfer-back`** |
| UUID | **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`** |
| LABEL | **setuphelfer-back** |
| FS | **ext4** |
| Device (Beispiel) | **`/dev/sdb1`** (kann wechseln) |

## Phase 1 — Ist-Zustand (Host, lesend)

### `systemctl cat setuphelfer-backend.service` (Kernaussage)

- **`User=setuphelfer`**, **`Group=setuphelfer`**, **`SupplementaryGroups=setuphelfer`**
- **`ProtectSystem=strict`**, **`ProtectHome=yes`**, **`PrivateTmp=yes`**, **`PrivateDevices=yes`**, **`NoNewPrivileges=true`**
- **`ReadWritePaths=`** (effektiv, `systemctl show`):  
  **`/opt/setuphelfer`** **`/etc/setuphelfer`** **`/var/log/setuphelfer`** **`/var/lib/setuphelfer`** **`/tmp`** **`/mnt`** **`/mnt/setuphelfer`**
- **`/media/gabriel/setuphelfer-back`** war **nicht** in `ReadWritePaths` enthalten.

### Shell — Mount

- **`findmnt`** / **`/proc/mounts`:** **`rw`** für **`/media/gabriel/setuphelfer-back`** (ext4, Quelle z. B. `/dev/sdb1`).

### API — `target-check` (vor Fix auf dem Host)

- **`mount.options`** in der Antwort: **`ro,...`**, **`mount_readonly": true`**
- **`write_test`:** **EROFS**, **`backup.backup_target_not_writable`**

### Backend-Version-Gate

- **`./scripts/check-backend-version-gate.sh`** → **Exit 0**
- **`GET /api/version`** → **HTTP 200**, schlanke JSON-Versionfelder.

## Ursachenanalyse

Unter **`ProtectSystem=strict`** sind Pfade außerhalb von **`ReadWritePaths`** im Service-Namespace **nicht beschreibbar** (häufig als **EROFS** sichtbar), selbst wenn der gleiche Pfad auf dem Host-**`/proc/mounts`** als **`rw`** erscheint.  
**`/media/...`** war nicht in **`ReadWritePaths`**; **`/mnt`** und **`/mnt/setuphelfer`** schon — daher wirkte es wie ein „rw vs. ro“-Widerspruch zwischen Shell und API.

## Phase 2 — `sudo -u setuphelfer` (Agent)

**Nicht ausführbar** (`sudo`: TTY/Passwort) — interaktiver Operator-Check ausstehend.

## Phase 3–4 — Korrekturpfad

### A) Repo (neue Paket-/Install-Generation)

In **`debian/setuphelfer-backend.service`** und **`setuphelfer-backend.service`** wurde **`/media/gabriel/setuphelfer-back`** an **`ReadWritePaths=`** angehängt (bestehende Einträge unverändert gelassen).

### B) Bereits installierter Host (Drop-in, Operator)

Beispiel-Datei im Repo: **`docs/operations/systemd/setuphelfer-backend-backup-target.conf.example`** → nach  
**`/etc/systemd/system/setuphelfer-backend.service.d/backup-target.conf`** kopieren, dann:

```bash
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
```

**Hinweis:** systemd führt mehrere **`ReadWritePaths=`**-Zuweisungen aus Unit + Drop-ins zusammen; ein Drop-in mit **nur** dem zusätzlichen Pfad ist üblich.

## Phase 5 — `target-check` nach Deploy (zu verifizieren auf dem Host)

Nach **`daemon-reload` + restart`** mit aktualisierter Unit oder Drop-in:  
**`GET …/target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0`** erneut — Erwartung: **kein** EROFS aus Sandbox für diesen Pfad (verbleibende Fehler wären dann echte Rechte/Mount-Themen).

**Im Agentenlauf:** kein zweiter `target-check`-Nachweis nach Live-Änderung an `/etc` (kein `sudo`).

## Phase 6 — BR-001

- **Kein** Backup gestartet.
- BR-001 bleibt **`blocked`**. **`ready_for_explicit_operator_approval`** erst nach separater, ausdrücklicher Betreiberfreigabe — **nicht** in diesem Lauf gesetzt.

## Referenzen

- **`BR-001_readonly_target_and_api500_analysis_2026-05-12.md`**
- **`BR-001_backend_update_and_version_fix_2026-05-13.md`**
