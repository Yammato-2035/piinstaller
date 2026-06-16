# R8E — MSI Boot: Chromium-Kiosk Crash-Loop (root ohne --no-sandbox)

**Version:** 1.7.18.5
**Hardware:** MSI GE63 Raider RGB 8RF, NVIDIA GTX 1070, Intel Core i7
**Symptom (Anwender):** Kein grafischer Boot, „blinkender Cursor", auf Shutdown eine
`debian-live-…`-Meldung.

## Befund (aus Hardware-Screenshot)

Konsole zeigt den Boot als erfolgreich (Kernel, live-boot, systemd laufen — Textausgabe
sichtbar, GPU funktioniert), aber dann eine **Endlosschleife** alle ~4 s mit jeweils neuer PID:

```
[FAILED] Failed to start setuphelfer-rescue-m..e - Setuphelfer Rescue Live Media Check.
[1549:1549:.../zygote_host_impl_linux.cc:101] Running as root without --no-sandbox is not supported.
[1611:1611:.../zygote_host_impl_linux.cc:101] Running as root without --no-sandbox is not supported.
...
```

Das ist **kein** GPU-/Treiberproblem. Die iwlwifi-Firmware- und SGX-Zeilen sind harmlos.

## Root Cause

Das Rescue-System läuft als **root**. Der Kiosk-Pfad
`etc/xdg/openbox/autostart` → `setuphelfer-rescue-kiosk-start` → `setuphelfer-rescue-ui-launch`
startete Chromium mit:

```
chromium --kiosk --app=http://127.0.0.1:8765/rescue.html
```

Chromiums Setuid-/Namespace-Sandbox (Zygote) **verweigert** den Start als root und beendet
sich sofort (crbug.com/638180). Der startende Dienst startet neu → Crash-Loop → nie ein
grafisches Bild → „blinkender Cursor".

### Warum die VM grün war, die Hardware nicht

In der QEMU-VM wurde der grafische X/Openbox-Kiosk-Pfad nicht durchlaufen (Login-Pfad statt
Kiosk), daher wurde Chromium nie als root gestartet. Auf echter Hardware mit realer GPU startet
X/Openbox → Autostart → Kiosk → Chromium-Crash-Loop. Der Bug war damit nur auf Hardware sichtbar.

## Fix

`setuphelfer-rescue-ui-launch`: Chromium wird für den Root-Kiosk mit pflichtigen Flags gestartet
(Source + gestagte Kopie unter `config/includes.chroot/usr/local/sbin/`):

```
chromium --no-sandbox --no-first-run --no-default-browser-check \
         --disable-gpu --disable-dev-shm-usage \
         --user-data-dir=/run/setuphelfer/chromium-profile \
         --kiosk --app=<URL>
```

- `--no-sandbox`: zwingend, sonst Root-Zygote-Crash-Loop.
- `--disable-gpu`: rescue bootet auf beliebigen GPUs (GTX 1070 nur nouveau/modesetting bzw.
  `nomodeset`/MSI-Compat). HW-GL kann dort hängen/schwarz bleiben; Software-Rendering ist der
  sichere, treiberfreie Weg.
- Firefox bleibt unverändert (kein Root-Sandbox-Problem).

## Regressions-Guard

`validate-controlled-live-build-tree.sh`: schlägt fehl, wenn der gestagte `ui-launch` kein
`--no-sandbox` an Chromium übergibt.

## Offene, nicht-blockierende Punkte

- `setuphelfer-rescue-media-check` meldet `[FAILED]` (nicht-fatal, Boot läuft weiter) — separat
  zu prüfen, ob auf echtem Stick relevant.
- `debian-live-…`-Meldung beim Shutdown ist üblicherweise kosmetisch (Overlay/Unmount).
