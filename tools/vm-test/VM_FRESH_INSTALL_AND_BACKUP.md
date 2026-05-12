# VM neu: Live-ISO → SSH-Keys → Setuphelfer (nur A) → Full-Backup → Restore-Zwischenschritt

Dieses Runbook setzt **beide** VMs (`setuphelfer-a`, `setuphelfer-b`) auf einen definierten **Neuanfang** mit **SSH per Key**, **deutscher Tastatur**, auf **A** zusätzlich **Setuphelfer**, danach **Full-Backup** auf der Backup-Platte und ein **isolierter Restore-Test** unter `/tmp` (ohne laufendes System zu überschreiben).

Schritte, die **Grafik / Installer** brauchen, sind **manuell** (VirtualBox-Konsole). Alles andere ist als Befehl dokumentiert.

---

## Phase 0 – Host: beide VMs für Live-Boot vorbereiten

ISO-Pfad anpassen (Beispiel, auf dem Referenzrechner vorhanden):

```bash
cd tools/vm-test
chmod +x scripts/*.sh
LIVE_ISO=/home/volker/Downloads/debian-live-13.4.0-amd64-xfce.iso ./scripts/12-vbox-both-live-install-prep.sh
```

Danach **nacheinander** starten (weniger RAM-Stress):

```bash
VM_NAME=setuphelfer-a ./scripts/03-vbox-start.sh
# Installation auf **A** fertig stellen, dann ggf. B:
# VM_NAME=setuphelfer-b ./scripts/03-vbox-start.sh
```

**„Could not read from the boot medium“** nach leerem DVD-Laufwerk: Systemplatte war nicht bootfähig — mit diesem Schritt bootet die VM wieder **sinnvoll** von der ISO; anschließend Debian **auf die Systemplatte** installieren (oder „Install Debian“ aus dem Live-Desktop).

---

## Phase 1 – Installation (manuell, Konsole)

- Auf **beiden** VMs dasselbe Konzept: Benutzer **`user`** (oder ein einheitlicher Name), Passwort **wie bisher bei der Live-ISO** beibehalten.
- Ziel: bootfähiges Debian auf **Port-0-Platte** (System-VDI), nicht nur Live-Sitzung ohne Installation.
- Nach Installation: einmal normal von **Platte** booten (Host: `10-vbox-eject-dvd-boot-disk.sh` + `03-vbox-start.sh`).

---

## Phase 2 – Gast: deutsche Tastatur + SSH-Key (beide VMs)

1. Public Key vom Host: `~/.ssh/id_ed25519.pub` (oder anderer Key) auf den Gast kopieren, z. B.:

   ```bash
   scp -o StrictHostKeyChecking=accept-new -P 2222 ~/.ssh/id_ed25519.pub volker@127.0.0.1:/tmp/
   ```

   Für **B** Port **2223** (NAT-Regel wie in eurer VBox).

2. **Im Gast** (sudo/root), Repo-Skripte verfügbar machen (Shared Folder oder `scp` des Ordners `tools/vm-test/scripts`).

3. Ausführen:

   ```bash
   sudo bash /pfad/zum/in-guest-vmtest-postinstall.sh /tmp/id_ed25519.pub volker
   ```

   Das setzt **de** per `localectl` und richtet **openssh-server** + **authorized_keys** wie in `SSH_UND_LOGIN.md` ein.

4. Vom Host testen:

   ```bash
   ssh -p 2222 -i ~/.ssh/id_ed25519 volker@127.0.0.1 true
   ssh -p 2223 -i ~/.ssh/id_ed25519 user@127.0.0.1 true
   ```

Optional: `host-ssh-fix-vm-test-vms.sh` anpassen (`VM_SSH_TARGETS`) und ausführen, wenn `scp`/`ssh` schon mit Passwort geht.

---

## Phase 3 – Nur **setuphelfer-a**: Setuphelfer installieren

Auf dem **Host** (Repo-Root = piinstaller):

```bash
cd /home/volker/piinstaller
tar czf /tmp/piinstaller-src.tgz --exclude=.git --exclude=node_modules --exclude=venv \
  --exclude=frontend/node_modules --exclude=dist .
scp -P 2222 /tmp/piinstaller-src.tgz volker@127.0.0.1:/tmp/
```

Auf **A** (per SSH):

```bash
mkdir -p /tmp/piinstaller-src && tar xzf /tmp/piinstaller-src.tgz -C /tmp/piinstaller-src
sudo env PI_INSTALLER_USER=user bash /tmp/piinstaller-src/scripts/install-system.sh
```

Hinweise: Internet im Gast; Dauer je nach CPU. Logs: `docs/SYSTEM_INSTALLATION.md`.

---

## Phase 4 – Beide: Testmarker und Backup-Mount (wie bisher)

Im Gast (root), Skript aus dem Repo:

```bash
sudo bash /tmp/piinstaller-src/tools/vm-test/scripts/in-guest-setup.sh
```

Backup-Disk partitionieren und nach `/mnt/backup-test` mounten: **`BACKUP_RUNBOOK.md`**.

---

## Phase 5 – Full-Backup (nur **A**, wo Setuphelfer läuft)

- Setuphelfer-UI oder API: **Full-Backup** nach `/mnt/backup-test/` (Ziel wie in den Reports).
- Oder klassisches `tar` laut Runbook — wichtig ist ein **`pi-backup-full-*.tar.gz`** mit eingebettetem Manifest (aktueller Setuphelfer-Stand).

---

## Phase 6 – Restore-Zwischenschritt (isolierter Test)

Auf **A** (oder vom Host per SSH), **ohne** `/` zu überschreiben:

```bash
sudo rm -rf /tmp/setuphelfer-restore-test
mkdir -p /tmp/setuphelfer-restore-test
cd /opt/setuphelfer/backend
python3 -c "
from pathlib import Path
from modules.restore_engine import restore_files
arch = Path('/mnt/backup-test/pi-backup-full-….tar.gz')  # echten Dateinamen einsetzen
td = Path('/tmp/setuphelfer-restore-test').resolve()
print(restore_files(arch, td, allowed_target_prefixes=(td,)))
"
```

Prüfungen: `find`, Marker unter `opt/setuphelfer-test/`, Symlinks — siehe frühere Restore-Checklisten.

---

## Phase 7 – Dauerhaft wieder von Platte booten

```bash
cd tools/vm-test
VM_NAME=setuphelfer-a ./scripts/10-vbox-eject-dvd-boot-disk.sh
VM_NAME=setuphelfer-b ./scripts/10-vbox-eject-dvd-boot-disk.sh
```

---

## Kurzüberblick Dateien

| Datei | Rolle |
|--------|--------|
| `scripts/12-vbox-both-live-install-prep.sh` | Beide VMs: aus + ISO + Boot DVD |
| `scripts/11-vbox-attach-live-iso-boot-dvd.sh` | Eine VM |
| `scripts/10-vbox-eject-dvd-boot-disk.sh` | ISO ab, Boot Platte zuerst |
| `scripts/in-guest-vmtest-postinstall.sh` | DE-Tastatur + SSH-Keys |
| `SSH_UND_LOGIN.md` | SSH-Details |
| `BACKUP_RUNBOOK.md` | Backup-Disk / Full-Backup |
