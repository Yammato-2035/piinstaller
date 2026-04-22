# Host-Ist-Prüfung: `setuphelfer-b` (VBox)

**Erzeugt:** 2026-04-19 (Host), nur **Host-/VBox-Lesung** und Dateisystem-Prüfungen.  
**Hinweis:** Dateiname bleibt `2026-04-18-setuphelfer-b-prepare-hostcheck.md` wie vorgegeben; Inhalt bezieht sich auf den **tatsächlichen** Prüfzeitpunkt.

---

## 1. VirtualBox-Konfiguration (`VBoxManage showvminfo setuphelfer-b`)

| Feld | Wert (Auszug) |
|------|----------------|
| **Zustand zum Zeitpunkt der ersten Abfrage** | `saved` (Zeitstempel in VBox-Ausgabe: 2026-04-19T10:06:46Z) – *danach für Kaltstart bewusst mit `discardstate` beseitigt, siehe andere Reports* |
| **RAM / CPUs** | 4096 MiB RAM, 2 CPUs (aus früherer VBox-Ausgabe; bei Bedarf erneut `showvminfo` fahren) |
| **Boot-Reihenfolge** | Boot1 = **DVD**, Boot2 = **HardDisk**, Boot3/4 = Not Assigned |
| **SATA Port 0** | `…/tools/vm-test/disks/system-b.vdi` |
| **SATA Port 1** | `…/tools/vm-test/disks/backup-b.vdi` |
| **SATA Port 2** | `…/tools/vm-test/disks/restore-target-b.vdi` |
| **SATA Port 3** | Zunächst **Empty**; später Live-ISO eingehängt (siehe Live-Vorbereitungs-Report) |
| **NIC1** | **NAT**, Cable connected **on** |
| **NAT-Portweiterleitung** | Regelname `guestssh`: TCP Host-Port **2223** → Gast-Port **22** (Host-IP in VBox-Ausgabe leer = alle Interfaces) |

---

## 2. Disk-Dateien (Host-Pfad `tools/vm-test/disks/`)

| Datei | Existenz | `VBoxManage showmediuminfo` (Auszug) |
|--------|----------|--------------------------------------|
| `system-b.vdi` | ja | State: **created**, Capacity **16384** MiB, dynamic |
| `backup-b.vdi` | ja | State: **created**, Capacity **8192** MiB, dynamic |
| `restore-target-b.vdi` | ja | State: **created**, Capacity **16384** MiB, dynamic |

**Dateigröße auf dem Host-Dateisystem:** jeweils ca. **2097152** Bytes (kleiner Footprint bei dynamischen VDI, zugewiesene Kapazität siehe oben).

---

## 3. Live-ISO (Host)

| Prüfung | Ergebnis |
|---------|----------|
| Pfad `/home/volker/Downloads/debian-live-13.4.0-amd64-xfce.iso` | **vorhanden**, Größe ca. 3.8 GiB |

---

## 4. Kurzfazit (nur Host)

- VM ist in VirtualBox **registriert**, mit **drei** Daten-VDIs + DVD-Slot, **NAT** und **2223→22**.
- **Port 3** war bei der ersten Abfrage **ohne** ISO; Kaltstart-Vorbereitung erforderte u. a. **ISO-Anbindung** und Entfernen des **saved state** (separat dokumentiert).
- **Kein** Nachweis eines installierten OS auf `system-b.vdi` aus dieser Host-Prüfung allein (VDI kann leer/unpartitioniert sein).
