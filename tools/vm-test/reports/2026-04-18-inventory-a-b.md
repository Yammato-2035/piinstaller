# Inventar setuphelfer-a / setuphelfer-b (2026-04-18)

**Quelle der Aussagen:** nur die Dateien  
`reports/inventory-setuphelfer-a-2026-04-18.txt` und  
`reports/inventory-setuphelfer-b-2026-04-18.txt` sowie die dort dokumentierten SSH-Fehlversuche.

**SSH:** Auf **setuphelfer-a** wurde `user@localhost` über Port **2222** verwendet (vom Nutzer mitgeteilt). Auf **setuphelfer-b** derselbe Benutzer über **2223**.

---

## Kurzstatus setuphelfer-a

| Thema | Beleg aus Report |
|--------|-------------------|
| **OS** | `PRETTY_NAME="Debian GNU/Linux 13 (trixie)"`, Kernel `6.12.73+deb13-amd64`; `IMAGE_ID=live`, `BUILD_ID=20260314T112523Z` → **Live-Image**, nicht ein installiertes Root-auf-Platte-System allein aus dem Report ableitbar |
| **Hostname** | `debian` |
| **Nutzer Inventur** | `user` |
| **setuphelfer** | `systemctl list-units`: `setuphelfer-backend.service` **loaded active running**; Prozess: `uvicorn app:app` unter `/opt/setuphelfer/backend/venv/` auf **127.0.0.1:8000** |
| **Platten lsblk** | `loop0` squashfs; `sda` ohne ausgefüllte Zeile im Ausschnitt; `sdb1` **ext4** auf **`/mnt/backup-test`**, ~7.4G frei; `sdc` ohne Zeile; `sr0` iso9660 Live-Medium |
| **Root-FS** | `/` ist **overlay** über squashfs + tmpfs-Overlay (typisch Live) |
| **Netz** | `enp0s3` 10.0.2.15/24 (NAT) |
| **Marker-Skript-Pfade** | `/opt/setuphelfer` und `/opt/testdata` sichtbar; **keine** expliziten Dateien `/opt/setuphelfer-test/marker.txt` im Report-Auszug (nur `ls -lah /opt`) |
| **/mnt** | `backup-test` vorhanden; zusätzlich Report zeigt `/mnt/backup-test` als Mount für sdb1 |

**Bereitschaft Backup (nur aus Belegen):** Ein separates **ext4**-Ziel **`/mnt/backup-test`** ist gemountet und hat freien Platz – erfüllt die Richtung „nicht nur Root-Overlay“. Ob die **Setuphelfer-UI/API**-Backup-Pipeline damit ohne Fehler durchläuft, ist **nicht** durch diesen Report belegt (kein Backup-Lauf).

---

## Kurzstatus setuphelfer-b

| Thema | Beleg |
|--------|--------|
| **Gast-Inventar** | **Nicht** vorhanden: SSH mit `user@localhost:2223` mehrfach **Timeout während Banner-Austausch** (siehe `inventory-setuphelfer-b-2026-04-18.txt`) |
| **VBox** | VM **running**; Platten `system-b.vdi`, `backup-b.vdi`, `restore-target-b.vdi`; Port 3 **leer**; NAT-Regel **2223→22** konfiguriert |

**Bereitschaft Restore:** Aus den Belegen **nicht** beurteilbar (kein SSH, kein `lsblk` im Gast). Remote-Inventur für Phase Restore **fehlt**.

---

## Unterschiede (faktenbasiert)

- **A:** vollständiger Shell-Inventar-Report; Live-System mit laufendem `setuphelfer-backend`; `user` per SSH nutzbar.
- **B:** nur Host-seitiger Stub-Report; **kein** Gast-Output.

---

## Risiken für Backup/Restore

1. **A läuft als Debian Live:** Root-Dateisystem ist **overlay**/squashfs – produktnahe „installierte Umgebung“ und Persistenz von `/opt` über Reboots sind **nicht** aus diesem Inventar allein abgeleitet.
2. **Backup-Ziel:** `/mnt/backup-test` ist **ext4** auf `sdb1` – passt zur erwarteten separaten Platte; Validierung der **Anwendung** (Mount-Sicherheit) wäre ein **eigener** Lauf.
3. **B ohne SSH:** Kein reproduzierbarer Remote-Testpfad auf **B** ohne Gast-Fix (z. B. `openssh-server`, OS-Installation, oder Konsole).

---

## Was für „Phase 3 (Backup)“ noch fehlt (checkliste, ohne Annahmen)

- [ ] Definierter **Full-Backup-Lauf** mit Setuphelfer auf **A** inkl. Log/Exit-Code (nicht Teil dieses Inventars).
- [ ] Klärung, ob Quelle bewusst **Live** bleiben soll oder installiertes System auf **sda** genutzt werden soll (dazu müsste `lsblk`/Boot auf **A** erweitert oder erneut gezogen werden – aktuell zeigt der Report `sda` ohne FSTYPE-Zeile).
- [ ] **B:** SSH-Zugang herstellen **oder** dokumentierte Alternative (serielle Konsole / nur VBox), erneut `guest_inventory.sh` ausführen und Report ersetzen/ergänzen **ohne** alte Logs zu überschreiben (neues Datums-Suffix).

---

*Kein Git-Commit durchgeführt.*
