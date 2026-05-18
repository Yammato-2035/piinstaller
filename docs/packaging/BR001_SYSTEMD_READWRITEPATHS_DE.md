# BR-001: systemd ReadWritePaths für externes Backup-Ziel

## Warum `ProtectSystem=strict` korrekt bleibt

Der Dienst `setuphelfer-backend.service` läuft mit **`ProtectSystem=strict`**. Das Dateisystem außerhalb der explizit freigegebenen Pfade ist für den Prozess nicht beschreibbar — ein bewusster Safety-Mechanismus gegen versehentliche oder kompromittierte Schreibzugriffe auf das laufende System.

Dieses Verhalten wird **nicht** abgeschwächt (kein `ProtectSystem=false`, kein globales `/`).

## Warum externe Backup-Ziele per `ReadWritePaths` freigegeben werden

Backup-Tar und der isolierte Runner schreiben als Nutzer **`setuphelfer`** auf ein **externes** Volume. Ohne Eintrag in **`ReadWritePaths=`** sieht der Dienst Mounts unter `/media/...` nicht zuverlässig — die API meldet dann z. B. **`BACKUP-TARGET-NOT-WRITABLE-002`** (`os.access`), obwohl Unix-Rechte am Mount stimmen.

## Warum nur `/media/setuphelfer/br001`

- **Enger Scope:** Nur der freigegebene BR-001-Zielpfad, nicht ganz `/media` oder `/`.
- Entspricht der Projektregel: externes Ziel **`/media/setuphelfer/br001`** auf **`/dev/sda1`**, nicht Root-FS.
- Weitere Pfade (z. B. `/opt/setuphelfer`, `/var/lib/setuphelfer`) bleiben in der Haupt-Unit bzw. anderen Drop-ins.

## Warum kein `/mnt/setuphelfer/backups`

Dieser Pfad liegt auf dem **internen** System-Dateisystem und ist durch Storage-Schutz zu Recht blockiert. BR-001 verlangt ein **externes** Medium.

## Warum kein chmod-/chown-Workaround

Breite Unix-Rechte (`777`) oder willkürliches `chown` umgehen nicht die **systemd-Sandbox** und schwächen Host-Sicherheit. Die korrekte Lösung ist ein **Drop-in** mit dokumentiertem `ReadWritePaths`.

## Drop-in im Repository

Datei: `packaging/systemd/setuphelfer-backend.service.d/backup-target-br001.conf`

```ini
[Service]
ReadWritePaths=/media/setuphelfer/br001
```

## Operator-Installation (Runtime)

```bash
cd /pfad/zum/piinstaller-repo
sudo mkdir -p /etc/systemd/system/setuphelfer-backend.service.d
sudo cp packaging/systemd/setuphelfer-backend.service.d/backup-target-br001.conf \
  /etc/systemd/system/setuphelfer-backend.service.d/br001-media-setuphelfer.conf
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
systemctl show setuphelfer-backend.service -p ReadWritePaths
curl -s "http://127.0.0.1:8000/api/backup/target-check?backup_dir=/media/setuphelfer/br001&create=0"
```

Erwartung Target-Check: **`status: success`**, Schreibtest ok, kein **`BACKUP-TARGET-NOT-WRITABLE-002`**.

## Verweise

- Evidence: `docs/evidence/runtime-results/br001_systemd_readwritepaths_dropin_2026-05-18.json`
- Externes Ziel: `docs/knowledge-base/storage/external-backup-target-architecture.md`
