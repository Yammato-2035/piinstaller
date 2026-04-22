# Recovery-Runbook (Zerstörung nur Testdisk, Rescue, Restore)

Alle Schritte auf dem **Host** in `tools/vm-test/`, sofern nicht anders vermerkt. Zerstörung **nur** `disks/system.vdi` mit explizitem Flag (Strict-Modus).

## 1. VM stoppen

```bash
cd tools/vm-test
./scripts/08-vbox-stop.sh
```

Bei hängender VM: `FORCE=1 ./scripts/08-vbox-stop.sh`

Warten, bis die VM wirklich aus ist (`VBoxManage showvminfo ... | grep State`).

## 2. System-Testdisk zerstören

Nur diese Datei, nur mit zweitem Argument `DESTROY_TEST_DISK` und Bestätigung `yes`:

```bash
./scripts/05-destroy-testdisk-safe.sh system.vdi DESTROY_TEST_DISK
```

Das Skript zeigt den **vollen Zielpfad** und bricht ab, wenn der Pfad nicht exakt `tools/vm-test/disks/system.vdi` (kanonisch) ist oder der Name nicht `system.vdi` lautet.

## 3. Rescue-ISO setzen

```bash
RESCUE_ISO=/ABSOLUTER/PFAD/rescue-oder-live.iso ./scripts/04-vbox-rescue-iso.sh
```

`RESCUE_ISO` muss ein existierender, absoluter Pfad sein.

## 4. VM starten

```bash
./scripts/03-vbox-start.sh
# oder headless:
HEADLESS=1 ./scripts/03-vbox-start.sh
```

## 5. Im Rescue-System

- Backup-Medium finden und mounten (entspricht **backup.vdi** / früher `/mnt/backup-test`-Inhalt).
- **Verify** gemäß Setuphelfer (Checksummen/Manifest).
- **Restore** auf die neue/leere **Systemplatte** starten (Setuphelfer-Doku beachten; ggf. neue `system.vdi` vor diesem Schritt neu anlegen, falls das Produkt eine leere Zielplatte erwartet — nach `05-destroy` fehlt die Datei).

**Hinweis:** Wenn nach Zerstörung keine `system.vdi` mehr existiert, muss vor Restore eine neue VDI erzeugt und in VirtualBox wieder als Port 0 eingehängt werden:

```bash
./scripts/01-create-disks-vbox.sh   # überspringt vorhandene; ggf. nur fehlende neu anlegen
# oder nur system.vdi manuell mit VBoxManage createmedium …
./scripts/02-vbox-define-vm.sh      # Medium wieder anbinden
```

Passe diesen Schritt an die **konkrete Setuphelfer-Restore-Anleitung** an.

## 6. Boot-Reihenfolge zurückstellen

Nach erfolgreichem Restore von der Platte booten — oder wenn die VM **wieder mit der Live-CD** startet (ISO noch an Port 3, `boot1=dvd`):

```bash
cd tools/vm-test
VM_NAME=setuphelfer-a ./scripts/10-vbox-eject-dvd-boot-disk.sh
```

Manuell (VM **aus**):

```bash
VM_NAME="${VM_NAME:-setuphelfer-recovery-test}"
VBoxManage storageattach "$VM_NAME" --storagectl SATA --port 3 --device 0 --type dvddrive --medium emptydrive
VBoxManage modifyvm "$VM_NAME" --boot1 disk --boot2 dvd
```

## 7. Neustart

VM neu starten, aus Platte booten, dann `VERIFY_CHECKLIST.md` abarbeiten.

## Diagnose (Host)

```bash
./scripts/09-collect-diagnostics.sh
```
