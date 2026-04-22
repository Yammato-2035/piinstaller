# Full-Restore + Boot-Test (Wissensbasis)

## Deutsch

Kurzfassung: Ein **Datei-Restore** auf eine zweite VM-Platte wurde durchgeführt, **GRUB** im Ziel-chroot installiert, anschließend die VM von der Restore-Platte gebootet und per **SSH** validiert (Hostname, Login, `sudo`). Details, Kommandos und Rohbefunde stehen im Prüfbericht:

- [../../tools/vm-test/reports/2026-04-21-full-restore-boot-test.md](../../tools/vm-test/reports/2026-04-21-full-restore-boot-test.md)

**Wichtig:** Ein reiner Datei-Restore repliziert den **gesicherten Softwarestand** des Quellsystems. Fehlen Setuphelfer-Pfade oder Units im Archiv, sind sie nach dem Boot **nicht** magisch wieder da — für den produktiven Setuphelfer-Endzustand ist die **Installer-Pipeline** (`scripts/install-system.sh`, systemd-Units) auf dem Zielsystem auszuführen. Der Bericht dokumentiert genau diese Nachinstallationsphase als **bewussten** Schritt.

**Bezug Release 1.5:** Deterministisches Verhalten = reproduzierbare Schritte (Restore → Boot-Check → optional erneute Installation der Setuphelfer-Services), keine ad-hoc „stillen“ API-Halberfolge bei Manifest/Gzip-Fehlern.

## English (short)

File-based restore to a second VM disk, GRUB installation in the target chroot, reboot from the restore disk, and SSH validation are recorded in the linked runbook above. Restoring files only restores what was in the archive; if Setuphelfer was not part of that snapshot, run `install-system.sh` on the target to reach the supported **systemd final state** (both `setuphelfer-backend` and `setuphelfer` active). This matches the **deterministic restore** story for release 1.5.0.0: fail-fast on bad archives, documented follow-up for services.
