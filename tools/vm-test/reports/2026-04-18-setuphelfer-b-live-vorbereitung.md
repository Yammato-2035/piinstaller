# setuphelfer-b: Live-Vorbereitung und Restore-Ziel-Modell (2026-04-19)

**Geltungsbereich:** Nur **belegbare** Host-/VBox-Aktionen und Messungen; **kein** erfolgreicher Gast-Shell-Zugriff in dieser Session.

**Kein Commit / kein Push.**

---

## 1. Hostseitig gefunden (Ist)

### VirtualBox `setuphelfer-b` (vor Intervention)

- Zustand war **`saved`** (VBox-Zeitstempel 2026-04-19T10:06:46Z).
- **Boot:** DVD zuerst, HDD zweit (bereits sinnvoll für Live).
- **SATA:** Port 0–2 → `system-b.vdi`, `backup-b.vdi`, `restore-target-b.vdi`; **Port 3 leer**.
- **NIC1:** NAT, Kabel an; NAT-Regel **guestssh: 2223 → 22** bereits gesetzt.
- **VDI-Kapazitäten (`showmediuminfo`):** system-b 16384 MiB, backup-b 8192 MiB, restore-target-b 16384 MiB; Zustand **created**.

### Host-Aktionen in dieser Vorbereitung (explizit)

| Aktion | Befehl / Effekt |
|--------|------------------|
| Saved State entfernen | `VBoxManage discardstate setuphelfer-b` → VM **powered off** (nur RAM-Zustand verworfen, **VDIs unverändert**) |
| Live-ISO einhängen | `VBoxManage storageattach … --port 3 --type dvddrive --medium /home/volker/Downloads/debian-live-13.4.0-amd64-xfce.iso` |
| Bootreihenfolge bestätigt | `VBoxManage modifyvm setuphelfer-b --boot1 dvd --boot2 disk` (entspricht Zielbild) |
| VM starten | `VBoxManage startvm setuphelfer-b --type headless` |
| Nach Start | `VBoxManage showvminfo`: **State: running** seit 2026-04-19T10:12:20Z |

---

## 2. Bootet B jetzt ins Live-System?

**Nachweisbar auf Host:** VM **läuft**, **dieselbe** Debian-Live-ISO wie auf Host A ist an **Port 3** gemountet, **Boot1 = DVD**.

**Nicht belegbar ohne Konsole/Screenshot:** Dass der Bootloader tatsächlich die ISO geladen hat und das Live-Desktop/Login erscheint (kein GUI-/Video-Capture in dieser Aktion).

---

## 3. Konnte B per SSH erreichbar gemacht werden?

**Nein (technisch belegt):** `ssh -p 2223 user@localhost` (BatchMode, mehrfache Wiederholungen) und `ssh -vv` zeigen: **TCP connect OK**, danach **kein** SSH-Server-Banner (Timeout). Damit ist **keine** remote lesende Inventur im Gast möglich gewesen.

**Kleiner Zusatzaufwand (nur dokumentiert, nicht ausgeführt):** In der **VBox-Konsole** im Live-System prüfen/starten des SSH-Dienstes, sofern im Image enthalten – siehe `inventory-setuphelfer-b-live-2026-04-18.txt`.

---

## 4. Welche Disks sind im Live-System sichtbar?

**Ohne Gast-Shell:** **nicht** bekannt (kein `lsblk` aus dem Gast in dieser Session).

**Nur aus VBox-Zuordnung (ohne /dev-Namen im Gast):**

| VBox SATA-Port | Medium-Datei (Host) | Rolle im Testkonzept (`tools/vm-test/README.md`) |
|----------------|---------------------|-----------------------------------------------------|
| 0 | `system-b.vdi` | vorgesehene **Systemplatte** / späteres Restore-Ziel für den Full-Test |
| 1 | `backup-b.vdi` | vorgesehenes **Backup-Medium** (Archiv-Ziel oder Transport-Medium) |
| 2 | `restore-target-b.vdi` | optionales **zweites Ziel** / spätere Stufen |
| 3 | Debian-Live ISO | **Live-System** zum Restore |

**`/dev/sda`/`sdb`-Reihenfolge im Gast:** aus diesen Daten **nicht** ableitbar → keine Benennung von „sda = …“ in diesem Bericht.

---

## 5. Restore-Zielmodell (Phase 5 – nur belegt + sauberste Konstellation)

### Belegt

- Die für den späteren Restore gedachte **System-VDI** ist **`system-b.vdi`** an **SATA Port 0** (erste angebotene Festplatte im Gast, subjektiv übliche Rolle „Zielplatte“).
- **Backup-Daten** für den A→B-Test müssen auf **B** physisch verfügbar sein: dafür ist **`backup-b.vdi`** (Port 1) vorgesehen (Kapazität 8192 MiB laut `showmediuminfo`).

### Sauberste Konstellation für den **ersten** A→B-Test (empfohlen, begründet ohne Gast-LSBLK)

1. **Restore-Ziel:** Inhalt/Partitionierung von **`system-b.vdi` (Port 0)** – dort soll das wiederhergestellte System landen; Platte sollte vor Restore **leer oder überschreibbar** sein (Zustand der Partitionierung aktuell **nicht** aus dem Gast belegt).
2. **Backup-Archiv:** Auf **`backup-b.vdi` (Port 1)** bereitstellen (z. B. Partition + Mount im Live, **nach** Gast-Inventur), damit es nicht mit dem Ziel-Device verwechselt wird.
3. **`restore-target-b.vdi`:** für den ersten Lauf **nicht** nötig; reduziert Verwechslungsrisiko, bis Gast-`lsblk` einmal sauber dokumentiert ist.

---

## 6. Eignung als Restore-Ziel-VM (ohne Restore-Anspruch)

| Kriterium | Stand |
|-----------|--------|
| Live bootbar aus ISO (Host-seitig) | **Vorbereitet** (ISO + Boot-Reihenfolge + VM running) |
| Remote-Inventur / Automation | **Nein** (SSH-Dienst am Gast nicht erreichbar) |
| Klare Plattenrollen in VBox | **Ja** (siehe Tabelle) |
| Restore-Fähigkeit / Boot nach Restore | **Nicht** geprüft und **nicht** behauptet |

---

## 7. Was fehlt vor dem Start des A→B-Tests

- [ ] **Gast-Inventur:** mindestens einmal `lsblk -f`, `blkid`, Mounts im **Live** (Konsole oder funktionierender SSH).
- [ ] **Backup-Archiv auf B verfügbar machen** (Kopie von A auf `backup-b.vdi` o. ä. – separater Plan).
- [ ] **Nach Restore:** Boot-Reihenfolge wieder **Platte zuerst**, ISO entfernen (Runbook-Pattern).
- [ ] Optional: **VBox-Snapshot** vor destruktivem Restore (aktuell laut früherer Prüfung oft keine Snapshots – explizit anlegen vor erstem Schreibzugriff auf `system-b.vdi`).

---

*Keine bestehenden Reports überschrieben; neue/neu benannte Dateien: Hostcheck, Live-Inventar-Stub, dieser Abschluss.*
