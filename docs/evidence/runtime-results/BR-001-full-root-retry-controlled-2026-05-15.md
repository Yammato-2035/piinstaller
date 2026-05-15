# BR-001 — Kontrollierter Full-Root-Retry (2026-05-15)

## Ergebnis: **failed** (USB stabil, Paket-Kollision)

| Kriterium | Ergebnis |
|-----------|----------|
| USB stabil | **Ja** (76 min, keine Kernel-Fehler sda/usb6) |
| Full-Archiv fertig | **Nein** |
| Verify deep | **Nein** |
| BR-001 Full validiert | **Nein** |

## Hardware (dokumentierte Topologie)

- **Änderung:** HDD von Hub `usb 1-2.1` → **Bus 006 Port 001 direkt**, UAS **5000M**
- **Platte:** HGST 1 TB, SABRENT-Bridge, `setuphelfer-back1` ext4 rw,noatime
- **SMART:** PASSED (Precheck)

## Lauf `4f2031bbe2f1`

- **Start:** 22:09:45 CEST  
- **Ende:** 23:25:48 CEST (**4562 s ≈ 76 min**)  
- **Geschrieben:** ~**97 GiB** (vor Abbruch)  
- **Kompression:** **gzip** (`tar -czf`), kein pigz  
- **Durchsatz:** Peak ~63 MiB/s, Mittel ~22 MiB/s  
- **RAM Runner:** ~22–23 GiB Peak  

## Abbruch-Ursache

`backup.blocked_package_activity` — **`apt-get install`** (mintupdate-automation-upgrade.timer ~23:25).  
Gate korrekt; `.partial` entfernt.

**Nicht** USB-Disconnect (im Gegensatz zum Lauf vom 15.05. 19:55).

## Kernel-Monitoring

`journalctl -kf` gefiltert: **keine** sda/usb6 disconnect/reset/I/O-Einträge im Backup-Fenster.

## Nächster Schritt

1. Vor Langlauf: `mintupdate-automation-upgrade.timer` / apt-Automation **pausieren** (manuell, dokumentiert)  
2. Full-Backup erneut starten  
3. Nach Erfolg: Verify deep → Restore Preview (separater Auftrag)

JSON: `BR-001-full-root-retry-controlled-2026-05-15.json`
