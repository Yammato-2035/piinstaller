# Warum EDID auf dem Raspberry Pi 5 nicht erzwungen werden kann

## Kontext

Unter **Wayland** kam der Sound aus den Gehäuselautsprechern; unter **X11** nicht. Das spricht für eine **Konfigurationssache**, nicht für Hardware. EDID soll HDMI-A-1 (für das Freenove Mediaboard) erzwingen, damit HDMI-Audio auch ohne Monitor/EDID funktioniert – aktuell gelingt das nicht zuverlässig.

---

## Ursache 1: `hdmi_edid_file` steht nicht in der `[hdmi0]`-Sektion

### Wie config.txt funktioniert

In `config.txt` gilt eine **Sektion** (z.B. `[hdmi0]`) nur für die **folgenden Zeilen bis zur nächsten Sektion**:

```ini
[hdmi0]
hdmi_force_hotplug=1
# ← Nur diese Zeile gehört zu [hdmi0]!

# HDMI1 (Port 2)
[hdmi1]
hdmi_force_hotplug=1
```

Alles, was **nach** der nächsten Sektion (z.B. `[hdmi1]`) oder in einem anderen Block steht, gilt **nicht** für HDMI0.

### Typischer Fehler

`hdmi_edid_file=1` und `hdmi_drive=2` werden oft **am Ende der Datei** oder in einem separaten Block ergänzt:

```ini
# PI-Installer: EDID für HDMI-A-1
[hdmi0]          # ← Neue Sektion, überschreibt vorherige!
hdmi_edid_file=1
hdmi_drive=2
```

Oder die Werte stehen **ohne** Sektion bzw. in einer anderen Sektion. Dann liest die Firmware sie **nicht** für HDMI0 und EDID wird nicht erzwungen.

### Richtige Konfiguration

Die EDID-Optionen müssen **direkt unter der bestehenden `[hdmi0]`-Sektion** stehen, ohne dazwischen eine neue Sektion:

```ini
# HDMI0 (Port 1)
[hdmi0]
hdmi_force_hotplug=1
hdmi_edid_file=1
hdmi_drive=2

# HDMI1 (Port 2)
[hdmi1]
hdmi_force_hotplug=1
```

Die EDID-Datei muss als `/boot/firmware/edid.dat` vorliegen (Firmware-Pfad auf Pi 5 / Bookworm).

---

## Ursache 2: Pi 5 + Bookworm ignoriert config.txt-EDID oft

### Bekanntes Verhalten

Auf **Raspberry Pi 5** mit **Raspberry Pi OS Bookworm** wird `hdmi_edid_file` in `config.txt` oft **nicht** ausgewertet bzw. EDID-Overrides werden ignoriert:

- DietPi-Forum: „Raspberry Pi 5 will not ignore EDID“
- Raspberry Pi Forums: „Bookworm EDID Troubles“, „RPi 5 HDMI issues“
- Nutzerberichte: Nach Bookworm-Updates wird die EDID-Datei nicht mehr geladen; in `dmesg` erscheint kein „Direct firmware load“ für die EDID

Das betrifft vor allem das **KMS/DRM-Setup** des Pi 5: Die Anzeige-/HDMI-Initialisierung läuft anders als auf Pi 4, die Firmware/Kernel werten config.txt-EDID-Optionen teils nicht (mehr) aus.

### Alternative: EDID per Kernel (drm.edid_firmware)

Statt config.txt kann die **Kernel-Kommandozeile** eine feste EDID-Datei erzwingen. Der Kernel sucht EDID-Dateien unter **/lib/firmware/** (nicht /boot/firmware).

**Schritte:**

1. **EDID-Binary ins System-Firmware-Verzeichnis:**

   ```bash
   # EDID von HDMI-A-2 (Monitor) kopieren
   sudo cp /boot/firmware/edid.dat /lib/firmware/edid-hdmi-a1.bin
   ```

2. **Kernel-Parameter in cmdline.txt ergänzen:**

   In `/boot/firmware/cmdline.txt` (eine Zeile) z.B. anhängen:

   ```
   drm.edid_firmware=HDMI-A-1:edid-hdmi-a1.bin
   ```

   Damit wird für den Connector **HDMI-A-1** die Datei `/lib/firmware/edid-hdmi-a1.bin` als EDID geladen.

3. **Prüfen nach Neustart:**

   ```bash
   dmesg | grep -i edid
   # Sollte z.B. "Direct firmware load for edid-hdmi-a1.bin" o.ä. zeigen
   ```

**Skript:** EDID nach `/lib/firmware/` kopieren und `drm.edid_firmware` in cmdline.txt setzen:

```bash
sudo ./scripts/fix-edid-via-kernel-cmdline.sh
sudo reboot
```

**Hinweis:** Auf einigen Pi-5/Bookworm-Setups wird auch `drm.edid_firmware` nicht zuverlässig angewendet. Dann bleibt nur, die Foren/Issues zu beobachten oder ein älteres Image zu testen.

---

## Was wir konkret tun

1. **config.txt korrigieren**  
   `hdmi_edid_file=1` und `hdmi_drive=2` werden **nur direkt in der bestehenden `[hdmi0]`-Sektion** eingetragen (direkt unter `hdmi_force_hotplug=1`), keine doppelte `[hdmi0]`-Sektion und keine EDID-Optionen „irgendwo“ in der Datei.

2. **Alternative drm.edid_firmware anbieten**  
   Skript/Anleitung: EDID nach `/lib/firmware/` kopieren und `drm.edid_firmware=HDMI-A-1:edid-hdmi-a1.bin` in `cmdline.txt` setzen (siehe oben).

3. **Wayland vs. X11**  
   Da unter Wayland die Lautsprecher funktionieren, zusätzlich prüfen:
   - Unter X11: Kein Skript/keine Einstellung darf HDMI-A-1 dauerhaft deaktivieren (z.B. `xrandr --output HDMI-1-1 --off` in `.xprofile` oder Autostart entfernen/anpassen).
   - Standard-Ausgabegerät auf HDMI-A-1 (Card 0) setzen, damit das Mediaboard Signal bekommt.

---

## Ein Skript für alles: enable-hdmi-a1-complete.sh

Damit HDMI-A-1 dauerhaft **enabled** bleibt und Ton aus den Gehäuselautsprechern kommt:

```bash
sudo ./scripts/enable-hdmi-a1-complete.sh
sudo reboot
```

Das Skript setzt in **cmdline.txt**:
- `video=HDMI-A-1:e` (Kernel aktiviert den Port beim Boot)
- `drm.edid_firmware=HDMI-A-1:edid-hdmi-a1.bin` (EDID aus `/lib/firmware/`)

und ergänzt in **config.txt** die erste `[hdmi0]`-Sektion um `hdmi_edid_file=1` und `hdmi_drive=2`.

**Nach dem Neustart unter X11:** `fix-x11-hdmi-a1-deactivation.sh` ausführen und danach **abmelden und wieder anmelden** (oder erneut reboot), damit `.xprofile` HDMI-A-1 nicht wieder ausschaltet.

---

## Kurzfassung

| Problem | Grund | Maßnahme |
|--------|--------|----------|
| HDMI-A-1 bleibt disabled | Kein `video=HDMI-A-1:e` oder EDID fehlt | `sudo ./scripts/enable-hdmi-a1-complete.sh` → Neustart |
| EDID wird nicht genutzt | `hdmi_edid_file=1` steht nicht **in** der `[hdmi0]`-Sektion | EDID-Zeilen direkt unter `[hdmi0]` und `hdmi_force_hotplug=1` eintragen |
| EDID wird trotzdem ignoriert | Pi 5 + Bookworm wertet config.txt-EDID oft nicht aus | `drm.edid_firmware` in cmdline.txt + EDID in `/lib/firmware/` (siehe Skript oben) |
| Sound nur unter Wayland | X11-Skripte oder Desktop schalten HDMI-A-1 aus | `fix-x11-hdmi-a1-deactivation.sh`, dann **ab- und wieder anmelden** |

Damit ist klar, **warum** EDID aktuell nicht erzwungen wird (Konfigurationsplatzierung + Pi-5/Bookworm-Verhalten) und welche Konfigurationsänderungen nötig sind.
