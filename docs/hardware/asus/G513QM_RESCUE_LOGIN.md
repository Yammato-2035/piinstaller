# G513QM Rescue login (Gabriel)

## Always try this first on Rescue / Emergency profiles

```text
1) Wenn „Give root password for maintenance“ / sulogin:
      → nur Enter drücken (leeres root-Passwort)

2) Wenn „login:“ erscheint:
      Benutzer: root
      Passwort: Enter (leer)

3) NICHT: Mint / MINT / mint als erstes bei sulogin
   (mint lowercase + leeres Passwort nur bei normalem getty)
```

## Nach erfolgreichem Rescue-Root

```bash
bash /media/volker/SETUP_LOGS*/setuphelfer/rog-pack/g513qm/scripts/setuphelfer-g513qm-capture.sh boot_early
# oder:
bash …/install-from-rescue.sh --mode inspect
```

Pfad ggf. anpassen (`findmnt -S LABEL=SETUP_LOGS`).

## Desktop/Installer erst danach

Nur auf **Hybrid Auto** oder **AMD Safe** (ohne nomodeset), aus der Rescue-Shell:

```bash
bash …/install-from-rescue.sh --mode graphics-preflight
bash …/install-from-rescue.sh --mode start-desktop
bash …/install-from-rescue.sh --mode installer-preflight
# nur wenn grün:
bash …/install-from-rescue.sh --mode ubiquity
```
