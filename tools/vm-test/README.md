# VM-Testumgebung: Full-Recovery (Setuphelfer)

Reproduzierbarer **Testpfad** auf einem Linux-Laptop: **Backup → Zerstörung der Systemplatte → Rescue-Boot → Restore → Neustart → Prüfung**.  
**VirtualBox** ist der vorgesehene Hypervisor; Orchestrierung: `./scripts/00-bootstrap-full-recovery-vbox.sh`.  
Detaillierte Schritte: `INSTALL_GUIDE.md`, `BACKUP_RUNBOOK.md`, `RECOVERY_RUNBOOK.md`, `VERIFY_CHECKLIST.md`.  
**SSH / Login-Probleme** (Keys, `sshd`, Konsole): **`SSH_UND_LOGIN.md`** und Skripte `scripts/in-guest-ensure-ssh-and-login.sh`, `scripts/host-ssh-fix-vm-test-vms.sh`. **Tastatur im VBox-Fenster:** Abschnitt *VirtualBox: Gast nimmt keine Tastatur an* in derselben Datei.  
**VMs neu mit Live-ISO, SSH-Keys, Setuphelfer, Backup/Restore:** **`VM_FRESH_INSTALL_AND_BACKUP.md`** sowie `scripts/11-vbox-attach-live-iso-boot-dvd.sh`, `scripts/12-vbox-both-live-install-prep.sh`, `scripts/in-guest-vmtest-postinstall.sh`.

**Reports (Ist-Zustände, Testpläne, ehrliche Laufberichte):** [`reports/`](reports/) – versionierbar; keine großen Logs (weiterhin `logs/` gitignored).

Alle destruktiven Schritte sind auf **`disks/system.vdi`** beschränkt (`05-destroy-testdisk-safe.sh`, Strict-Modus). **Keine** Skripte hier installieren Host-Pakete oder schreiben auf Host-Platten (`/dev/sd*`).

**Docker Desktop auf demselben Host:** Eine laufende VirtualBox-VM kann KVM blockieren und Docker Desktop mit `qemu … exit status 1` beenden. VM zuerst herunterfahren, dann Docker Desktop starten. Doku, FAQ und Wissensdatenbank: [`docs/host-env/`](../../docs/host-env/README.md).

## Phase 1 – Host-Ist (Referenz, Stand Prüfung im Repo)

Vor Nutzung lokal verifizieren:

```bash
for c in qemu-system-x86_64 qemu-img virt-install virsh virt-manager VBoxManage kvm; do
  command -v "$c" && echo "  OK $c" || echo "  fehlt: $c"
done
grep -E 'vmx|svm' /proc/cpuinfo | head -1
groups | grep -q kvm && echo "Nutzer in Gruppe kvm" || echo "nicht in Gruppe kvm (für /dev/kvm)"
ls -la /dev/kvm 2>/dev/null || true
```

**Auf dem Referenzrechner:** QEMU/libvirt-Befehle waren **nicht** im PATH; **`VBoxManage`** (VirtualBox) war verfügbar. **CPU-Virtualisierung (svm/vmx)** vorhanden; **`/dev/kvm`** fehlte bzw. Nutzer nicht in `kvm` — für den dokumentierten Pfad ist **VirtualBox** der praktikable Einstieg ohne neue Host-Pakete.

## Phase 2 – Verzeichnisstruktur

```
tools/vm-test/
  README.md                 # Überblick
  INSTALL_GUIDE.md          # ISO + Debian-Installation (BIOS)
  BACKUP_RUNBOOK.md         # Backup im Gast
  RECOVERY_RUNBOOK.md       # Zerstörung nur system.vdi, Rescue, Restore
  VERIFY_CHECKLIST.md       # Boot-Nachweis / Marker
  disks/                    # lokale VDI (gitignored, außer .gitkeep)
  scripts/
    lib/common.sh           # Pfade, require_cmd
    00-bootstrap-full-recovery-vbox.sh  # Phase 1–3 + Log
    01-create-disks-vbox.sh
    01-create-disks-qemu.sh # nur wenn qemu-img existiert
    in-guest-setup.sh       # im Gast ausführen (Marker, /mnt/backup-test)
    in-guest-ensure-ssh-and-login.sh  # im Gast als root (openssh-server, Keys, Shell)
    host-ssh-fix-vm-test-vms.sh       # auf dem Host (beide VMs anstoßen, wenn SSH erreichbar)
    02-vbox-define-vm.sh
    03-vbox-start.sh
    04-vbox-rescue-iso.sh
    05-destroy-testdisk-safe.sh
    06-vbox-snapshot.sh
    07-archive-test-disk.sh
    08-vbox-stop.sh
    09-collect-diagnostics.sh
    10-vbox-eject-dvd-boot-disk.sh  # ISO von Port 3 entfernen, wieder von Systemplatte booten
    11-vbox-attach-live-iso-boot-dvd.sh  # Live-ISO einhängen, Boot zuerst DVD (Neuinstallation)
    12-vbox-both-live-install-prep.sh   # setuphelfer-a + b: aus + ISO + Boot DVD
    in-guest-vmtest-postinstall.sh      # Gast: DE-Tastatur + SSH-Keys (ruft ensure-ssh auf)
```

## Phase 3 – VM-Disks

| Datei (unter `disks/`) | Rolle | Default-Größe (VBox) |
|----------------------|--------|----------------------|
| `system.vdi` | Hauptsystem (Installation, später Zerstörung) | 8192 MiB |
| `backup.vdi` | Backup-Zielmedium | 512 MiB |
| `restore-target.vdi` | Optionales zweites Ziel / Restore-Tests | 512 MiB |

QEMU-Variante: `system.qcow2`, `backup.qcow2`, `restore-target.qcow2` (`01-create-disks-qemu.sh`).  
Größen per Umgebung: `SYS_MB`, `BACKUP_MB`, `REST_MB` bzw. `SYS_GB`, …

## Phase 4 – Gastsystem-Plan (manuell im Installer)

**Erster Testlauf:** Debian 12 Netinst, **BIOS**, eine Root-Partition ext4 — siehe `INSTALL_GUIDE.md`.  
**Marker und Mount-Punkt** im Gast: `sudo bash scripts/in-guest-setup.sh` (Pfad im Gast anpassen).

**Backup-Disk im Gast:** siehe `BACKUP_RUNBOOK.md` (Partition auf zweiter Platte, Mount `/mnt/backup-test`).

**Hinweis:** OS-Installation und Setuphelfer im Gast **nicht** durch Host-Skripte automatisiert.

## Phase 5 – Recovery-Testpfad (Ablauf)

1. **VM anlegen & Platten:** `./scripts/00-bootstrap-full-recovery-vbox.sh` (oder `01` + `02` einzeln)
2. **Installations-ISO** an Port 3 hängen (siehe Ausgabe von `02-vbox-define-vm.sh`), `03-vbox-start.sh` (oder `HEADLESS=1 ./03-vbox-start.sh`)
3. Im Gast: System fertig installieren, Marker anlegen, Backup-Zielplatte einrichten, **Backup mit Setuphelfer** (oder Test-Äquivalent) auf `backup.vdi` schreiben
4. **Optional vor Zerstörung:** `06-vbox-snapshot.sh take pre-wipe` und/oder `08-vbox-stop.sh` dann `07-archive-test-disk.sh system.vdi ARCHIVE_TEST_DISK`
5. **VM stoppen:** `08-vbox-stop.sh` (bei Bedarf `FORCE=1`)
6. **Nur system.vdi zerstören:** `05-destroy-testdisk-safe.sh system.vdi DESTROY_TEST_DISK` — Strict: nur dieser Name, nur `tools/vm-test/disks/`, `yes` nötig
7. **Rescue:** `RESCUE_ISO=/abs/pfad.iso ./04-vbox-rescue-iso.sh`, VM starten, Restore ausführen
8. **Boot-Reihenfolge** nach Restore wieder auf Platte: z. B. `VBoxManage modifyvm "$VM_NAME" --boot1 disk --boot2 dvd`
9. **Erfolg:** Marker-Dateien und Diensteverhalten prüfen

## Sicherheit (Zerstörung)

- `05-destroy-testdisk-safe.sh`: **ausschließlich** `system.vdi`, nur wenn `VM_TEST_DISKS` kanonisch `tools/vm-test/disks` ist; zweites Argument `DESTROY_TEST_DISK`; Bestätigung `yes`.
- Pfade mit `..` werden abgelehnt (`resolve_disk_path` in `lib/common.sh`).

Nach kritischen Schritten: `./scripts/09-collect-diagnostics.sh` (Log unter `logs/`).

## Phase 6 – Hilfsskripte (ohne Gast-Paketinstallation)

| Skript | Zweck |
|--------|--------|
| `00-bootstrap-full-recovery-vbox.sh` | Ist-Prüfung, 01+02, Log in `logs/` |
| `01-create-disks-vbox.sh` | VDIs erzeugen |
| `02-vbox-define-vm.sh` | VM registrieren, Platten + leeres DVD-Laufwerk |
| `03-vbox-start.sh` | Start (optional `HEADLESS=1`) |
| `04-vbox-rescue-iso.sh` | `RESCUE_ISO=` absolut setzen |
| `05-destroy-testdisk-safe.sh` | Zerstörung nur Allowlist + Bestätigung |
| `06-vbox-snapshot.sh` | Snapshot take/list/restore/delete |
| `07-archive-test-disk.sh` | Kopie einer Allowlist-Datei mit Zeitstempel |
| `08-vbox-stop.sh` | ACPI shutdown; `FORCE=1` poweroff |
| `09-collect-diagnostics.sh` | Log unter `logs/` |
| `10-vbox-eject-dvd-boot-disk.sh` | ISO abbinden, `--boot1 disk` (nach Live/Rescue-Zeit wieder normales System) |
| `11-vbox-attach-live-iso-boot-dvd.sh` | `LIVE_ISO=` einhängen, `--boot1 dvd` (Neustart / Neuinstallation) |
| `12-vbox-both-live-install-prep.sh` | Beide VMs wie oben (Standardnamen **a**/**b**) |
| `13-vm-autopilot-status.sh` | Ein-Befehl-Status beider VMs (VBox-State, Boot, ISO, SSH-Port, Key-Login) |
| `in-guest-ensure-ssh-and-login.sh` | Gast: `sshd`, Drop-in-Config, `authorized_keys`, Shell/Konto (siehe `SSH_UND_LOGIN.md`) |
| `host-ssh-fix-vm-test-vms.sh` | Host: gleiches Skript per `scp`/`ssh` auf **a** (2222) und **b** (2223) |

## Phase 7 – Abschlussbericht (Vorlage)

1. **Virtualisierung:** QEMU/libvirt im PATH? VirtualBox? KVM-Gerät?
2. **Neu angelegt:** Pfade unter `tools/vm-test/…`
3. **Testpfad:** VBox mit drei VDI + Rescue-ISO-Schritten wie oben
4. **Manuell:** Gast-OS installieren, Marker, fstab/Backup-Disk, Setuphelfer-Backup/Restore, ISO-Beschaffung, Boot-Reihenfolge nach Restore
5. **Risiken/Lücken:** z. B. kein KVM, VDI-Kopie bei laufender VM, Restore-ISO muss zum Backup-Format passen, UEFI vs BIOS inkonsistent

---

*Keine automatische Paketinstallation durch diese Skripte. Host-Root und Host-Platten werden nicht angesprochen.*
