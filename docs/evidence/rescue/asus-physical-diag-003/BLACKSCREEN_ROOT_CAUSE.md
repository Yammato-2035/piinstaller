# Blackscreen / kein TUI — Root Cause

## Was belegt ist

1. Korrekter GRUB-Eintrag `hardware_discovery` (MSI-Lab aus, auto_shutdown=0).
2. Maschine G513QM / BIOS 331.
3. dmesg: **`Console: switching to colour dummy device 80x25`** während amdgpu-Modeset → Panel schwarz.
4. **nouveau und amdgpu** gleichzeitig geladen (Discovery-Eintrag hatte kein nouveau-Blacklist).
5. systemd: journald-Start-Timeout, udev-settle failed, `graphical.target initializing`.
6. Nur **early**-Diagnostics; kein full boot, keine TUI, kein hardware_discovery-Capture.

## Was das Herunterfahren erklärt

`setuphelfer_auto_shutdown=0` — kein Lab-Auto-Shutdown. Wahrscheinlicher: Boot hängt (graphical.target/journald),
Operator sieht nichts und hält Power, oder Residual-Timer/Deadline. Nicht als erfolgreicher Capture werten.

## Fix für nächsten Boot

GRUB Hardwarediagnose mit: `nomodeset modprobe.blacklist=nouveau nouveau.modeset=0`
plus Textmodus erzwingen (`setuphelfer_mode=text`), kein GUI.
