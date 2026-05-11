# Installation der Test-VM (halbautomatisch)

Die VM-Platten und die VirtualBox-VM werden durch `./scripts/00-bootstrap-full-recovery-vbox.sh` angelegt. **Du** wählst nur die ISO und führst den Installer durch.

## Empfehlung

- **Debian 12** — [Netinst-ISO](https://www.debian.org/CD/netinst/) (`amd64`)
- **Firmware:** in VirtualBox **BIOS** belassen (erster Testlauf ohne UEFI), damit Partitionierung und GRUB einfach bleiben.

## VirtualBox: ISO einhängen

```bash
cd tools/vm-test
VM_NAME="${VM_NAME:-setuphelfer-recovery-test}"
VBoxManage storageattach "$VM_NAME" --storagectl SATA --port 3 --device 0 --type dvddrive --medium /ABSOLUTER/PFAD/debian-12.x.y-amd64-netinst.iso
./scripts/03-vbox-start.sh
```

## Installer (Debian)

1. Sprache/Tastatur nach Wunsch.
2. **Partitionierung:** manuell oder „Geführt“ — **eine Root-Partition** (ext4), gesamte `system.vdi` nutzen; kein separates `/home` nötig für den Minimaltest.
3. Bootloader: Standard (GRUB auf der Platte) — bei BIOS ohne zusätzliche ESP nötig.
4. **Benutzer (Vorschlag, nur Test-VM):**
   - Benutzername: `testuser`
   - Passwort: `testpass`
5. Software-Auswahl: Standard-Systemwerkzeuge reichen; **OpenSSH-Server** im Installer mit anwählen (oder später `scripts/in-guest-ensure-ssh-and-login.sh` laut **`SSH_UND_LOGIN.md`**).

## Nach dem ersten Boot (im Gast)

Setuphelfer-Testdaten und Mount-Punkt vorbereiten:

```bash
# Als root (oder mit sudo):
sudo bash /pfad/zum/in-guest-setup.sh
```

Falls du das Skript per SCP/Shared Folder bereitstellst, Pfad anpassen. Details zu Markern siehe `VERIFY_CHECKLIST.md`.

## Logging (Host)

Nach Installation oder bei Problemen auf dem Host:

```bash
cd tools/vm-test
./scripts/09-collect-diagnostics.sh
```

Ausgabe unter `logs/diagnostics-*.txt`.
