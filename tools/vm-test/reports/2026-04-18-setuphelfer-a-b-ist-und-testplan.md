# Ist-Zustand `setuphelfer-a` / `setuphelfer-b` und Testplan (Stand 2026-04-18)

**Erstellt:** automatisierte Host-/VBox-Prüfung aus dem Repo-Arbeitsverzeichnis  
**Wichtig:** Es wurde **kein** Gastsystem gestartet, **kein** Restore und **kein** Backup ausgeführt.  
**Grund:** `setuphelfer-a` ist im Zustand **saved** (SSH-Portweiterleitung inaktiv); ohne expliziten Start/Resume ist keine Remote-Inventur im Gast möglich.

---

## Phase 0 – Regeln und reale Umgebung (heute geprüft)

| Prüfung | Ergebnis |
|----------|----------|
| Host | `Linux … 6.8.0-110-generic`, x86_64 |
| `VBoxManage` | vorhanden |
| `qemu-system-x86_64`, `qemu-img` | vorhanden |
| `virt-install`, `virsh` | **nicht** im PATH |
| `ssh`, `scp`, `python3`, `git` | vorhanden |
| VMs in VirtualBox | `setuphelfer-a`, `setuphelfer-b` **registriert** |
| DNS `setuphelfer-a` / `setuphelfer-b` | **nicht** auflösbar (kein Eintrag in dieser Umgebung) |
| SSH Gast über `localhost:2222` | **Connection refused** (VM nicht laufend → NAT-Regel inaktiv) |

**Repo:** `tools/vm-test/` enthält Runbooks (`INSTALL_GUIDE.md`, `BACKUP_RUNBOOK.md`, `RECOVERY_RUNBOOK.md`, `VERIFY_CHECKLIST.md`), Skripte und `disks/`.  
**Hinweis:** `tools/vm-test/.gitignore` ignoriert `disks/*`, `logs/`, `*.log` – **VDI-Inhalte und Lauf-Logs sind nicht versioniert**; dieser Bericht beschreibt nur Metadaten und VBox-Ausgaben.

---

## Phase 1 – Zustandscheck VirtualBox (beide VMs)

### Gemeinsam

- **Snapshots:** bei beiden VMs laut `VBoxManage snapshot … list`: *keine Snapshots*
- **CPU/RAM:** je 2 vCPUs, 4096 MiB RAM
- **Grafik:** VBoxVGA, PS/2-Maus

### `setuphelfer-a`

| Aspekt | Befund |
|--------|--------|
| **Zustand** | **saved** seit `2026-04-15T18:13:19Z` |
| **Boot-Reihenfolge** | **1 = DVD**, **2 = HardDisk** (Live-ISO hat Boot-Priorität vor Platte) |
| **SATA Port 0** | `tools/vm-test/disks/system.vdi` (Dateigröße auf Host aktuell **~2 MiB** – dynamisches VDI, effektiver Inhalt u. a. im **Save-State** `.sav`) |
| **SATA Port 1** | `tools/vm-test/disks/backup.vdi` (~25 MiB) |
| **SATA Port 2** | `tools/vm-test/disks/restore-target.vdi` (~2 MiB) |
| **SATA Port 3** | **ISO eingehängt:** `…/Downloads/debian-live-13.4.0-amd64-xfce.iso` |
| **Netzwerk** | **NIC1 NAT**, Kabel an; **Portweiterleitung** `127.0.0.1:2222 → Gast:22` |
| **Save-State** | unter `~/VirtualBox VMs/setuphelfer-a/Snapshots/` liegt eine **~1,9 GiB** `.sav`-Datei (RAM/VM-Zustand) |

**Interpretation:** Zum Zeitpunkt des Speicherns war vermutlich ein **Live-/Installationskontext** aktiv oder die Boot-Reihenfolge bevorzugt DVD. Für ein „laufendes Linux mit Setuphelfer als Quelle“ muss im Gast **geprüft** werden: tatsächlich installiertes OS auf `system.vdi`, Setuphelfer-Dienste, Marker, Backup-Pfad – **heute nicht nachweisbar ohne Gast-Start.**

### `setuphelfer-b`

| Aspekt | Befund |
|--------|--------|
| **Zustand** | **powered off** seit `2026-04-15T17:18:16Z` |
| **Boot-Reihenfolge** | **1 = DVD**, **2 = HardDisk** |
| **SATA Port 0** | `tools/vm-test/disks/system-b.vdi` (~2 MiB) |
| **SATA Port 1** | `tools/vm-test/disks/backup-b.vdi` (~2 MiB) |
| **SATA Port 2** | `tools/vm-test/disks/restore-target-b.vdi` (~2 MiB) |
| **SATA Port 3** | **leer** |
| **Netzwerk** | **alle NICs disabled** → **kein SSH/NAT** solange nicht umkonfiguriert |

**Interpretation:** Ziel-VM ist für **Remote-Orchestrierung aktuell ungeeignet**, bis mindestens eine NIC (typ. NAT + optional dieselbe 2222-Regel wie bei A) aktiviert ist. Ohne Netz bleibt nur **VBoxManage-GUI** oder **serielle Konsole** / **VBox-API**.

---

## Phase 1 – Was ist brauchbar / was fehlt (ehrlich)

### Bereits brauchbar (Host-/VBox-Ebene)

- Beide VMs existieren; Platten-Layout entspricht dem **Drei-Platten-Modell** (System / Backup / Restore-Ziel) aus `tools/vm-test/README.md` (bei B mit `-b`-Suffix-Dateien).
- Auf **A** existiert eine **Debian-Live-13.4 Xfce-ISO** als Medium (Pfad dokumentiert oben).
- Skripte und Checklisten im Repo beschreiben einen **referenzierbaren** Recovery-Pfad (VBox, `system.vdi`-Zerstörung nur mit `05-destroy-testdisk-safe.sh` usw.).

### Nicht nachgewiesen (heute)

- Ob auf **A** ein **installiertes** Debian mit **Setuphelfer** läuft und ob das im Save-State der **Platte** oder nur der **Live-Sitzung** steckt.
- Ob bereits **vollständige** Backup-Archive auf `backup.vdi` liegen (VDI-Größe allein belegt keinen Inhalt).
- Ob **B** nach Restore **bootfähig** wäre (kein Test).
- **Kein** erfolgreicher End-to-End-Nachweis A→Live→B→Reboot in dieser Session.

### Handlungsbedarf vor dem ersten echten A→B-Lauf

1. **Klärung Boot/Medium A:** Entscheidung, ob Quelle = installiertes OS auf Port 0 oder Live-Session; ggf. ISO von Port 3 entfernen und Boot auf **HardDisk zuerst**, wenn die Quelle die installierte Platte ist.
2. **Netz B:** NIC1 aktivieren (NAT), optional identische SSH-Forward-Regel (z. B. Host-Port **2223**→22), damit Skripte wie auf A nutzbar sind.
3. **Snapshots (empfohlen):** Vor destruktiven Schritten auf **B** (und ggf. A) benannte Snapshots anlegen – aktuell **keine**.
4. **Gast-Inventur (Remote):** `A` starten oder gespeicherten Zustand **resume**n, dann `ssh -p 2222 localhost` und im Gast: `os-release`, `systemctl status setuphelfer-backend`, Marker aus `VERIFY_CHECKLIST.md`, `lsblk`, Mounts, freier Platz auf Backup-Volume.
5. **Backup-Ziel:** Sicherstellen, dass das vom Setuphelfer gewählte Archiv auf **separatem** Block-Volume liegt (Produktlogik: Mount-Validierung; siehe `docs/developer/BACKUP_RECOVERY_ENGINES.md`).

---

## Phase 2 – Testarchitektur (reproduzierbar, Zielbild)

**Quelle – `setuphelfer-a`**

- Installiertes Linux (empfohlen: Debian 12 wie `INSTALL_GUIDE.md`), Setuphelfer wie in Produktions-/Testdoku.
- **Marker:** wie `in-guest-setup.sh` / `VERIFY_CHECKLIST.md` (`/opt/setuphelfer-test/marker.txt`, `/etc/setuphelfer-test.conf`); erweiterbar um Nutzerdateien unter `/home/…`.
- **Vergleichskriterien (Soll):** Marker-Inhalt, wesentliche Paket-/Dienstzustände (definieren, was „identisch“ vs. tolerabel ist: z. B. neue MAC → `udev`, Journal-Zeilen).

**Backup**

- **Full-Backup** mit Setuphelfer auf **gemountetes** separates Medium (Port 1), nicht Root-FS.
- Artefakte: `tar.gz` (o. ä.), **Manifest/Verify** laut Engine-Doku; Logs im Gast oder über journald.
- Abbruch, wenn Zielmedium ungeeignet (bereits im Produktcode angelegt).

**Ziel – `setuphelfer-b`**

- **Live booten** (ISO an Port 3, Boot-Reihenfolge DVD zuerst – entspricht aktuellem Default).
- Restore-Komponente (`recovery/main.py` / UI-Flow laut Repo) mit **eindeutig** gewählter Zielplatte (Port 0).
- Nach Restore: Boot-Reihenfolge **Disk zuerst**, ISO entfernen oder leer; **Cold Boot** von `system-b.vdi`.
- **Nachweis:** Login, Marker-Dateien, kritische Dienste; optional `verify_deep` gegen Archiv (Host-seitig mit kopiertem Archiv).

**Toleranzen / Testfehler**

- Tolerabel: Zeitstempel, Journal-Rotation, neue SSH-Host-Keys.
- Testfehler: fehlende Marker, fehlender Setuphelfer, nicht bootendes System, falsches Root-FS nach Restore.

---

## Phase 3–4 – Vorbereitung und Live-Restore (Skizze, nicht ausgeführt)

- Marker auf A anlegen/verifizieren (`in-guest-setup.sh` im Gast).
- Backup auf `backup.vdi`-Partition (Runbook `BACKUP_RUNBOOK.md`).
- Archiv + Logs auf Host oder zweites Medium kopieren (z. B. `scp` von A), nach B bringen (z. B. gemeinsames `backup-b.vdi` befüllen oder Netzfreigabe – **Konkretisierung im nächsten Schritt**).
- B: ISO mounten, Live starten, Restore ausführen, Boot testen.

---

## Phase 5 – Fehlerprotokoll (heute)

| # | Beschreibung | Reproduzierbar | Ursache (wahrscheinlich) | Status |
|---|----------------|----------------|---------------------------|--------|
| F1 | SSH `localhost:2222` schlägt fehl | ja | VM **saved**/nicht laufend → NAT-Regel nicht aktiv | offen bis VM-Start |
| F2 | Hostname `setuphelfer-a/b` nicht pingbar | ja | keine lokale DNS-/hosts-Zuordnung | erwartbar; über IP/NAT arbeiten |
| F3 | Kein Gast-Status Setuphelfer/Marker | — | keine Gast-Session gestartet (Vorgabe) | bewusst offen |

---

## Phase 6 – Erweiterte Stufen (Reihenfolge laut Aufgabe)

1. Restore auf zweites Laufwerk (`restore-target-b.vdi` / Port 2).  
2. Virtuelle Cloud (eigene VM + WebDAV o. ä., **Secrets nicht im Repo**).  
3. IONOS reale Cloud (Testumgebung zuerst).  
4. Verschlüsselte Backups + Fehlerfälle Schlüssel.  
5. Schlüssel auf USB (Prozess + Failure-Modes).  
6. Raspberry Pi: eigene Hardware-/Image-Matrix (nicht mit x86-VDI vermischen).

---

## Phase 7 – Zusatztests (Matrix, mit bestehenden Produktpunkten verknüpft)

| Thema | Bezug Repo / Produkt |
|--------|----------------------|
| Separates Backup-Ziel | Backend: Mount-Validierung, UI-Meldungen `backup.messages.backup_target_*` |
| Speicher voll | `_do_backup_logic` / `backup.no_space` |
| Ungültiges/unvollständiges Archiv | `backup_verify`, Restore-Blockaden |
| Abgebrochener Restore | Restore-Engine / UI-Abbruch (gezielt testen) |
| Cloud ohne Netz / falsche Credentials | `recovery_transport`, UI-Codes |
| Falsche Verschlüsselung | `backup_crypto` / UI |
| Symlinks / Sonderdateien | `BACKUP_RECOVERY_ENGINES.md`, Tests |
| Bootloader / BIOS vs UEFI | Runbooks: konsistent **BIOS** oder gezielt UEFI dokumentieren |
| Ungeeignete Zielpfade | implementierte Validierung |

---

## Phase 8 – Automatisierung (ohne heute umzusetzen)

- Host-Skripte: nur `VBoxManage`, `ssh`, `scp` – **keine** stillen `VBoxManage unregistervm` / keine Zerstörung ohne `DESTROY_TEST_DISK`.
- Gast: idempotente Marker-Skripte, Backup-API oder CLI (falls vorhanden) **mit Logdatei unter `/tmp` oder Nutzer-Home**, dann Kopie per `scp`.
- Reports: **dieses Verzeichnis** `tools/vm-test/reports/` (versionierbar); große Logs weiterhin unter `logs/` (gitignored) optional zusätzlich kopieren.

---

## Phase 9 – Dokumentation (Änderungen heute)

- Neuer Bericht: **diese Datei** `tools/vm-test/reports/2026-04-18-setuphelfer-a-b-ist-und-testplan.md`
- Kurzverweis: `tools/vm-test/README.md` (Abschnitt „Reports“)

FAQ/Wissensdatenbank/Changelog: **keine** inhaltliche Erweiterung in dieser Session (kein nachgewiesener Lauf).

---

## Phase 10 – Abschlussbericht (ehrlich)

1. **Ist-Zustand VMs:** siehe Tabellen oben (VBox); Gast-OS/Setuphelfer **nicht** verifiziert.  
2. **Heute real geprüft:** Host-Tooling, VM-Registrierung, Storage-Anbindung, Boot-Reihenfolge, NAT/SSH auf A, fehlende NICs auf B, VDI-Dateigrößen, fehlende Snapshots, fehlgeschlagener SSH-Versuch.  
3. **Erfolgreich:** konsistente Dokumentation des **Ist-Zustands** und eines **Wiederholungsplans** ohne Datenverlust.  
4. **Fehlgeschlagen / nicht ausgeführt:** Gast-Inventur, Backup, Restore, Boot-Nachweis A→B.  
5. **Fixes:** keine Code-/VM-Änderungen vorgenommen (Vorgabe: Zustand zuerst dokumentieren).  
6. **Nächste Tests:** VM A starten/resumen → SSH-Inventur → Boot-Reihenfolge/Medium klären → B Netz aktivieren → Snapshots → Runbook-Schritte.  
7. **Risiken:** Save-State kann veralteten Zustand einfrieren; kleine `system*.vdi` auf Host können irreführend sein (dynamisch + `.sav`); B ohne Netz = hoher manueller Aufwand.  
8. **Commit-/push-reif:** nur **Dokumentation** (`reports/*.md` + README-Verweis); **kein Commit** durchgeführt.

---

## Commit-Vorschlag (nur Text, nicht ausgeführt)

```text
docs(vm-test): Ist-Bericht setuphelfer-a/b und A→B-Testplan (2026-04-18)

- Neuer Report unter tools/vm-test/reports/
- README: Verweis auf Reports
```
