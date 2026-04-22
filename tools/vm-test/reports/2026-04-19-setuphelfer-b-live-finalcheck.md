# setuphelfer-b — Live-Finalcheck (2026-04-19)

**Quellen:** `inventory-setuphelfer-b-live-2026-04-19.txt`, die darin referenzierten PNG-Dateien unter `tools/vm-test/reports/`, sowie die fehlgeschlagenen `VBoxManage guestcontrol`-Ausgaben.

**Kein Commit.**

---

## 1. Bootstatus: Live-System läuft ja/nein

| Frage | Befund |
|--------|--------|
| Boot erfolgreich (Menü → System) | **Ja, belegbar:** Nach `keyboardputscancode 1c 9c` existiert `setuphelfer-b-xfce-live-2026-04-19.png` mit deutlich größerer Datei als das vorherige GRUB-Bild (127840 Bytes vs. 61491 Bytes). |
| Grafische Oberfläche (XFCE) sichtbar | **Ja, belegbar am PNG:** sichtbar u. a. XFCE-typisches Layout, Panel „Applications“, Dock mit Terminal-Icon, Schriftzug **„Debian Live user“** und Datum **2026-04-19** in der Leiste. |
| GRUB vor dem Start | **Ja, belegbar am PNG:** `setuphelfer-b-grub-2026-04-19.png` zeigt das Bootmenü mit hervorgehobenem Eintrag **„Live system (amd64)“**. |

---

## 2. Laufwerke: welches Device ist Zielplatte / Backup-Platte

| Frage | Befund |
|--------|--------|
| `lsblk -f` aus dem Gast | **Nein** — in `inventory-setuphelfer-b-live-2026-04-19.txt` ist dokumentiert, dass `VBoxManage guestcontrol` mit Fehler **„guest execution service is not ready (yet)“** endet. Damit liegen **keine** Gast-`lsblk`-Rohdaten vor. |
| Zuordnung **/dev/sdX** → VDI | Aus diesem Lauf **nicht** belegbar (ohne `lsblk`). |
| Zuordnung **nur VirtualBox (Host)** | **Belegbar** aus früheren Host-Reports (unverändert): SATA Port **0** → `system-b.vdi`, Port **1** → `backup-b.vdi`, Port **2** → `restore-target-b.vdi`, Port **3** → Debian-Live-ISO. |

---

## 3. Restore-Voraussetzung: technisch bereit ja/nein

| Kriterium | Urteil (nur auf Basis der Belege) |
|-----------|-------------------------------------|
| Live-System bootfähig und sichtbar | **Ja** (Framebuffer-PNGs). |
| Datenträger im **Gast** sichtbar (`lsblk`) | **Nein** (keine Ausgabe; guestcontrol nicht nutzbar). |
| **Gesamt „technisch bereit für Restore“** | **Teilweise:** Live-Oberfläche steht, aber die geforderte **Festplatten-Sicht im Gast** ist **nicht** nachgewiesen → **kein vollständiges „ja“**. |

---

## 4. Offene Punkte vor dem A→B-Test

1. Im **Gast-Terminal** (VBox-Konsole, Symbolleiste): `lsblk -f`, `mount | head -30`, `df -h`, `ip a`, `uname -a`, `cat /etc/os-release` ausführen und Ausgabe **als neue Datei** (neues Datum im Namen) ins Repo übernehmen — **ohne** bestehende Reports zu überschreiben.  
2. Optional: **VBox Guest Additions** bleiben unangetastet (keine Installation laut Vorgabe); ohne GA bleibt `guestcontrol` i. d. R. unbrauchbar.  
3. **SSH** weiterhin optional; für den Nachweis ist die **Konsole** ausreichend, sobald Rohdaten kopiert sind.

---

## Anhang: erzeugte Artefakte (Dateien)

- `tools/vm-test/reports/setuphelfer-b-grub-2026-04-19.png`
- `tools/vm-test/reports/setuphelfer-b-xfce-live-2026-04-19.png`
- `tools/vm-test/reports/inventory-setuphelfer-b-live-2026-04-19.txt`
