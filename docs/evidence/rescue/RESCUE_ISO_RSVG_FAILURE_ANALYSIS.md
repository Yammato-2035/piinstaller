# Rescue ISO rsvg Failure Analysis

**Datum:** 2026-05-25  
**Git HEAD:** `fe36af0`  
**Status:** `ANALYZED_NOT_FIXED`

## Exakter Fehler

Der echte Operator-Build endete mit:

```text
/usr/bin/env: 'rsvg': No such file or directory
LB_EXIT=127
```

## Ausloesender Build-Schritt

Der `rsvg`-Aufruf stammt nicht aus einem Setuphelfer-Backend-, Frontend- oder Rescue-Skript. Die relevante Stelle liegt in der installierten `live-build`-Toolchain des Hosts:

- `/usr/lib/live/build/lb_binary_syslinux`

Dort wird fuer das Syslinux/Isolinux-Bootmenue aus `splash.svg.in` ein PNG-Bootsplash erzeugt:

- `config/bootloaders/isolinux/splash.svg.in`
- `binary/isolinux/splash.svg.in`

Die `live-build`-Logik erzeugt zuerst `splash.svg` und ruft anschliessend `rsvg --format png --height 480 --width 640 ...` auf.

## Welche Datei / welcher Hook loest den Aufruf aus

Ausloeser ist die `live-build`-Phase `lb_binary_syslinux` beim Bearbeiten des Bootloader-Themes `live-build`.

Belastbare Befunde:

- im Build-Tree existiert `config/bootloaders/isolinux/splash.svg.in`
- im installierten Host-Skript `/usr/lib/live/build/lb_binary_syslinux` ist der `rsvg`-Aufruf explizit enthalten
- dasselbe Host-Skript prueft fuer das Theme `live-build` explizit auf `rsvg` bzw. `librsvg2-bin`

Damit ist der `rsvg`-Aufruf eindeutig der Bootloader-Splash-Konvertierung von `live-build` zuzuordnen, nicht Tauri, nicht dem Dashboard und nicht einem Setuphelfer-Hook.

## Host-Tool vorhanden?

Geprueft:

- `command -v rsvg` -> **kein Treffer**
- `command -v rsvg-convert` -> **kein Treffer**

Damit ist mindestens klar: Auf dem Host ist derzeit weder `rsvg` noch `rsvg-convert` verfuegbar.

## Chroot-Tool vorhanden?

Nicht belastbar nachgewiesen.

Ohne neuen instrumentierten Build darf nicht behauptet werden, ob `rsvg` nur auf dem Host fehlt, nur im chroot fehlt oder in beiden Kontexten fehlt.

Belastbar ist nur:

- `live-build` erwartet fuer diesen Schritt `rsvg`
- der reale Build brach genau an einem `rsvg`-Aufruf ab
- Host-`rsvg` ist definitiv nicht vorhanden

## Benoetigtes Paket

Die installierte `live-build`-Implementierung verweist selbst auf:

- `librsvg2-bin`

Dieses Paket stellt den von `live-build` erwarteten `rsvg`-Befehl bereit.

Wichtig:

- Es wurde **kein** `apt install` ausgefuehrt.
- Diese Analyse dokumentiert nur den Befund.

## Alternative ohne Paketinstallation

Moegliche Fix-Richtungen, **noch nicht ausgefuehrt**:

1. `live-build` so konfigurieren, dass die `splash.svg.in`-zu-`splash.png`-Konvertierung nicht mehr gebraucht wird.
2. Das Bootloader-Theme `live-build` ersetzen oder anpassen.
3. Ein fertiges PNG bereitstellen und die SVG-basierte Generierung aus dem Buildpfad entfernen.
4. Theme-/Bootsplash-Erzeugung fuer den Rescue-Build deaktivieren, falls das Release-Gate das zulaesst.

## Fazit

Der aktuelle Failure ist kein unspezifischer "SVG-Fehler", sondern ein konkreter `live-build`-Bootloader-Schritt:

- Datei-/Theme-Pfad: `config/bootloaders/isolinux/splash.svg.in`
- Toolchain-Schritt: `/usr/lib/live/build/lb_binary_syslinux`
- benoetigtes Tool: `rsvg` aus `librsvg2-bin`

Der naechste erlaubte Schritt ist deshalb:

- **`fix_missing_rsvg_or_remove_rsvg_dependency`**

Kein neuer ISO-Build wurde fuer diese Analyse gestartet.
