# R8G — Dedizierte Log-Partition + Früh-Marker (garantierte Offline-Diagnose)

Version: 1.7.19.2

## Problem

Trotz der Persistenz-Korrektur in 1.7.19.1 (`_rw_usable`-Schreibtest, `remount,rw`
des Live-Mediums) blieb der Stick nach drei MSI-Boots (GE63 Raider, i7, GTX 1070)
**leer** (`setuphelfer/diagnostics/` nicht vorhanden). Symptom am Gerät:

- GRUB erscheint nur als **Textmenü** (kein grafisches Theme).
- Standard-Eintrag → sofort **blinkender Cursor**, kein sichtbarer Text.
- Kompatibilitätsmodus (`nomodeset`) → Text sichtbar bis zur **iwlwifi/WLAN-Meldung**,
  dann hängend.

Damit ist offen, ob der Hänger **vor systemd** (Kernel/initramfs/KMS) liegt oder ob
das System läuft und nur die **Konsole unsichtbar** ist (i915-KMS schaltet den
Framebuffer schwarz) bzw. das **Persistieren weiter scheitert**.

Die Ursache des leeren Sticks ist mit hoher Wahrscheinlichkeit, dass ein
`remount,rw` des read-only Live-Mediums auf dieser Firmware/USB-Kombination **still
fehlschlägt** — alle Logs landen im RAM und sind nach dem Ausschalten weg.

## Lösung

### 1. Dedizierte, immer beschreibbare Log-Partition (`SETUPHELFER_LOGS`)

Der Writer (`write-fat32-esp-rescue-usb.sh`) legt jetzt eine **zweite GPT-Partition**
über den restlichen Stick-Speicher an:

```
sgdisk -n 2:0:0 -t 2:0700 -c 2:SETUPHELFER_LOGS   # vfat, mkfs.vfat -F32 -n SETUPHELFER_LOGS
```

live-boot fasst diese Partition **nie** an (sie enthält kein `/live`). Ein frischer
`mount -t vfat -o rw` darauf ist deshalb **echt read-write** — kein gemeinsamer
read-only-Superblock wie beim Live-Medium. Das ist das einzige Ziel, das auch dann
zuverlässig persistiert, wenn das `remount,rw` des Live-Mediums scheitert.

`setuphelfer-rescue-boot-diagnostics` priorisiert dieses Ziel als **Stufe 0** in
`ensure_esp_rw()` (vor Live-Medium-remount und RAM-Fallback), inklusive
Schreibtest (`_rw_usable`).

### 2. Früh-Marker (`...-early.service`, sysinit-Stufe)

Neue Unit `setuphelfer-rescue-boot-diagnostics-early.service`:

- `WantedBy=sysinit.target`, `After=systemd-udev-settle.service`,
  `DefaultDependencies=no`, **nicht** `Before=sysinit.target` (darf den Boot nie
  blockieren).
- Ruft `setuphelfer-rescue-boot-diagnostics early` — eine **schnelle**, leichte
  Erfassung (Meta, geladene Netz/GPU-Module, systemd-Status, dmesg-Tail), schreibt
  sofort und beendet, bevor die schweren `journalctl`/`dmesg`-Captures laufen.

Damit ist der Stick nach dem nächsten Boot ein **eindeutiger Indikator**:

| Befund auf dem Stick (`setuphelfer/diagnostics/`) | Schlussfolgerung |
|---|---|
| **gar nichts** (auch kein `*_early`) | Hänger **vor systemd** (Kernel/initramfs/KMS) → Kernel-Parameter nötig |
| nur `*_early` vorhanden | Hänger **zwischen sysinit und multi-user** |
| `*_early` + `*_boot`/`latest` | systemd läuft; Problem ist nur die **Anzeige** (KMS-Blank) oder ein späterer Dienst |

### 3. Stufen / Capture-Punkte gesamt

- `early` (sysinit) — schnell, garantiert früh.
- `boot` (`...-diagnostics.service`, multi-user) — vollständige Matrix.
- Timer (`OnBootSec=15s`, `OnUnitActiveSec=15s`) — wiederholt.
- `shutdown` (`...-diagnostics-shutdown.service`) — letzter Stand beim Herunterfahren.

Alle Phasen schreiben bevorzugt auf `SETUPHELFER_LOGS`, dann Live-Medium, dann RAM,
und `sync`en zum physischen Stick.

## Validator-Guards (neu)

`validate-controlled-live-build-tree.sh`:

- `boot-diagnostics` muss `SETUPHELFER_LOGS` bevorzugen und die `early`-Phase
  unterstützen.
- `...-early.service` + `sysinit.target.wants`-Symlink müssen vorhanden sein.
- `write-fat32-esp-rescue-usb.sh` muss die `SETUPHELFER_LOGS`-Partition anlegen.

## Nachtrag (FAT-Label-Bug, erster Schreibversuch 1.7.19.2)

Erster MSI-Boot mit der 2-Partitionen-ISO kam **deutlich weiter**: systemd lief, das
TUI startete, die WLAN-Passwortabfrage erschien — wurde aber regelmäßig durch
„FAT-fs … bogus"-Kernelmeldungen unterbrochen. Ursache (aus `write_steps.log`):

```
+ sudo mkfs.vfat -F 32 -n SETUPHELFER_LOGS /dev/sdb2
mkfs.vfat: Label can be no longer than 11 characters
FAILED_STEP=mkfs_logs
```

FAT-Volume-Labels sind auf **11 Zeichen** begrenzt; `SETUPHELFER_LOGS` (16) wurde
abgewiesen → `sdb2` blieb **ohne Dateisystem**. Der GPT-Partitionsname darf 16 Zeichen
haben (Partition existierte), aber die Diagnose fand beim Mounten kein FS → Kernel
spammt „bogus" auf die Konsole (alle 15 s durch den Timer), Diagnose fiel in den RAM
zurück (verloren).

Fix:

- Writer: FAT-Label der Log-Partition auf **`SETUP_LOGS`** (10 Zeichen) verkürzt; der
  GPT-Partlabel bleibt `SETUPHELFER_LOGS` (so findet die Diagnose sie via
  `/dev/disk/by-partlabel/`). **Kein ISO-Rebuild nötig** — der Diagnose-Code in der
  ISO lokalisiert die Partition bereits über den Partlabel.
- Writer-Guard: nach `mkfs` wird jetzt geprüft, dass die Log-Partition tatsächlich
  `vfat` trägt (sonst harter Abbruch), damit ein FS-Fehler nie mehr still durchläuft.
- Diagnose: Suchreihenfolge auf `by-partlabel/SETUPHELFER_LOGS` zuerst, plus
  `by-label/SETUP_LOGS` (greift bei künftigen Builds).

**Wichtige Erkenntnis:** Der Boot erreicht das Userspace-TUI bis zur WLAN-Abfrage —
der „blinkende Cursor" der Vorversionen war also primär ein Anzeige-/KMS-Thema, nicht
ein echter früher Hänger. Mit gültiger Log-Partition werden jetzt erstmals echte
Diagnosedaten erwartet.

## Durchbruch (1.7.19.3): erste echte Diagnosedaten vom MSI

Mit gültiger Log-Partition lieferte der MSI erstmals vollständige Diagnosen
(`SETUP_LOGS/setuphelfer/diagnostics/*`, je `early` + `boot` über mehrere Boots).
Auswertung (GE63 Raider RGB 8RF, BIOS E16P5IMS.109, Kernel 6.1):

**Befund 1 — media-check Fehlalarm.** `media-check` schlägt mit
`SQUASHFS_SPOT_CHECK_FAILED` (exit 16) fehl, OBWOHL `squashfs_hash_ok: true`
(sha256 exakt) und `required_files_ok: true`. Die Spot-Checks via
`unsquashfs -cat <image> <pfad>` scheitern für **alle** Pfade (nmcli, curl, Skripte,
boot-branding) — `-cat` wird nicht unterstützt/scheitert an Symlinks. Folge: „Live-
Medium nicht stabil"-Dialog, `start-assistant` stoppt → **Hänger bei Eintrag 1**.
Fix: Bei stimmendem Gesamt-Hash (fat32_esp) ist das Medium beweisbar intakt; der
Spot-Check ist nur noch **beratend** und blockiert die Stabilität nicht mehr
(`setuphelfer-rescue-live-medium-check.py`, Regressionstest ergänzt).

**Befund 2 — Chromium-Kiosk crash-loopt ohne X.** `setuphelfer-rescue-ui.service`
lief mit `ConditionKernelCommandLine=!setuphelfer_start_assistant=1` (also in Compat-,
Diagnose-, RAM-Eintrag) und startete Chromium `--kiosk` ohne X-Server →
„Missing X server or $DISPLAY … platform failed to initialize. Exiting." → Restart
alle 3 s → tty1-Spam → **Hänger/„BOGUS"-Eindruck bei Eintrag 3**. Fix: Kiosk ist
jetzt **opt-in** via `ConditionKernelCommandLine=setuphelfer_kiosk=1`; Standard ist
das Text-TUI.

**Befund 3 — Compat-Eintrag ohne TUI.** Der MSI/NVIDIA-Kompatibilitätseintrag hatte
kein `setuphelfer_start_assistant=1` → weder TUI noch (jetzt) Kiosk. Fix: Compat- und
RAM-Eintrag bekommen `setuphelfer_start_assistant=1`
(`generate_fat32_esp_grub_cfg` / `generate_grub_cfg`).

Zusätzliche Erkenntnis: Framebuffer = „EFI VGA" (efifb), i915/nouveau laden, aber
unter `nomodeset` übernimmt KMS nicht — die Textkonsole funktioniert (TUI-Dialoge
sichtbar). WLAN-Hardware ok (`wlo1`, iwlwifi `iwlwifi-9000-...ucode` direct-loading;
nur optionales `iwl-debug-yoyo.bin` fehlt = harmlos).

## Status

- prepare + validate (Tree) **grün** (1.7.19.2).
- Nächster Schritt: ISO bauen → Stick schreiben (jetzt mit 2. Partition) → MSI booten
  (beide Einträge testen) → Stick zurück → `setuphelfer/diagnostics/` auslesen.
