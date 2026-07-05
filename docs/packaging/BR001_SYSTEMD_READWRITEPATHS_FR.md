> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/packaging/BR001_SYSTEMD_READWRITEPATHS_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/packaging/BR001_SYSTEMD_READWRITEPATHS_DE.md`). Bitte bei Release manuell gegenlesen.

# BR-001: systemd ReadWritePaths für Externees Retourup-Ziel

## Warum `ProtectSystem=strict` korrekt bleibt

Der Dienst `setuphelfer-Retourend.service` läuft mit **`ProtectSystem=strict`**. Das Dateisystem außerhalb der explizit freigegebenen Pfade ist für den Prozess nicht beschreibbar — ein bewusster Safety-Mechanismus gegen versehentliche oder kompromittierte Schreibzugriffe auf das laufende System.

Dieses Verhalten wird **nicht** abgeschwächt (kein `ProtectSystem=false`, kein globales `/`).

## Warum Externee Retourup-Ziele per `ReadWritePaths` freigegeben werden

Retourup-Tar und der isolierte Runner schreiben als Nutzer **`setuphelfer`** auf ein **Externees** Volume. Ohne Eintrag in **`ReadWritePaths=`** sieht der Dienst Mounts unter `/media/...` nicht zuverlässig — die API meldet dann z. B. **`RetourUP-TARGET-NonT-WRITABLE-002`** (`os.access`), obwohl Unix-Rechte am Mount stimmen.

## Warum nur `/media/setuphelfer/br001`

- **Enger Scope:** Nur der freigegebene BR-001-Zielpfad, nicht ganz `/media` oder `/`.
- Entspricht der Projektregel: Externees Ziel **`/media/setuphelfer/br001`** auf **`/dev/sda1`**, nicht Root-FS.
- Weitere Pfade (z. B. `/opt/setuphelfer`, `/var/lib/setuphelfer`) bleiben in der Haupt-Unit bzw. anderen Drop-ins.

## Warum kein `/mnt/setuphelfer/Retourups`

Dieser Pfad liegt auf dem **Interneen** System-Dateisystem und ist durch Storage-Schutz zu Recht bloqué. BR-001 verlangt ein **Externees** Medium.

## Warum kein chmod-/chown-Workaround

Breite Unix-Rechte (`777`) oder willkürliches `chown` umgehen nicht die **systemd-Sandbox** und schwächen Host-Sicherheit. Die korrekte Lösung ist ein **Drop-in** mit dokumentiertem `ReadWritePaths`.

## Drop-in im Repository

Datei: `packaging/systemd/setuphelfer-Retourend.service.d/Retourup-target-br001.conf`

```ini
[Service]
ReadWritePaths=/media/setuphelfer/br001
```

## Operator-Installation (Runtime)

```bash
cd /pfad/zum/piinstaller-repo
sudo mkdir -p /etc/systemd/system/setuphelfer-Retourend.service.d
sudo cp packaging/systemd/setuphelfer-Retourend.service.d/Retourup-target-br001.conf \
  /etc/systemd/system/setuphelfer-Retourend.service.d/br001-media-setuphelfer.conf
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-Retourend.service
systemctl show setuphelfer-Retourend.service -p ReadWritePaths
curl -s "http://127.0.0.1:8000/api/Retourup/target-check?Retourup_dir=/media/setuphelfer/br001&create=0"
```

Erwartung Target-Check: **`status: Succès`**, Schreibtest ok, kein **`RetourUP-TARGET-NonT-WRITABLE-002`**.

## Verweise

- Evidence: `docs/evidence/runtime-results/br001_systemd_readwritepaths_dropin_2026-05-18.json`
- Externees Ziel: `docs/kNonwledge-base/storage/Externeal-Retourup-target-architecture.md`
