# R8C — MSI Boot-Hang Root Cause & Fix

**Datum:** 2026-06-14
**Version:** 1.7.18.0 → **1.7.18.1** (Bugfix)
**Profil:** `standard`
**Symptom (Operator MSI):** GRUB startet (textuell), Auswahl „Rescue" / „Rescue mit Netzwerk" hängt; `setuphelfer-rescue-qemu-smoke…` Service startet nicht, Folge-Service startet nicht, TUI-Menü wird nie erreicht.

## Root Cause

Die ausgelieferte `standard`-ISO enthielt **veraltete `developer-qemu`-Artefakte**, die auf echter Hardware den Boot blockieren.

| Artefakt in der squashfs | Datum | Befund |
|---|---|---|
| `etc/systemd/system/multi-user.target.wants/setuphelfer-qemu-smoke-autopilot.service` | 2026-06-04 | Service **aktiviert** (`WantedBy=multi-user.target`) |
| `etc/systemd/system/setuphelfer-qemu-smoke-autopilot.service` | 2026-06-01 | Unit **ohne** `ConditionVirtualization=qemu` |
| `usr/local/sbin/setuphelfer-qemu-smoke-autopilot.sh` | 2026-06-04 | Script vorhanden → `ConditionPathExists` erfüllt |
| `etc/systemd/system/setuphelfer-dev-agent.service` | 2026-06-04 | Stale (nicht aktiviert, Hygiene) |

### Warum es hängt
Die Unit prüfte nur:
```
ConditionPathExists=/opt/setuphelfer-rescue            # immer erfüllt
ConditionPathExists=/usr/local/sbin/setuphelfer-qemu-smoke-autopilot.sh   # leider auch erfüllt
```
Es gab **keinen** `ConditionVirtualization=qemu`-Guard. Auf der MSI:
- `Wants=network-online.target` → wartet auf Netzwerk
- Script verbindet zu QEMU-Host `http://10.0.2.2:8001` → auf realer Hardware nicht erreichbar → Hänger/Fehler
- `TTYPath=/dev/ttyS0` + `StandardOutput=tty` auf nicht vorhandener serieller Konsole

Da der Service `Type=oneshot` mit `WantedBy=multi-user.target` ist, blockiert er `multi-user.target`. Der `setuphelfer-rescue-start-assistant` (`Before=getty@tty1`, `Conflicts=getty@tty1`) wird nie sauber erreicht → **kein Menü**. Exakt das beobachtete Verhalten.

### Wie das Leck entstand
`copy_profile_overlay()` kopiert per `rsync` `developer-qemu`-Dateien nach `config/includes.chroot/`. Beim Wechsel zurück auf `standard` entfernte der Prepare-Lauf **nur** die `serial-boot-markers`-Symlink — die Autopilot-Artefakte blieben liegen und wurden in die `standard`-ISO eingebacken. Beide ISO-Validatoren prüften das Leck **nur** im `developer-qemu`-Zweig, nie für `standard` → der Defekt wurde nie gemeldet.

## Fix (Defense-in-Depth)

1. **Guard in der Unit-Quelle** — `build/rescue/profiles/developer-qemu/includes.chroot/etc/systemd/system/setuphelfer-qemu-smoke-autopilot.service`:
   `ConditionVirtualization=qemu` ergänzt → läuft **nie** auf realer Hardware, selbst wenn das Artefakt erneut leakt.

2. **Purge im Prepare** — `scripts/rescue-live/prepare-controlled-live-build-tree.sh`:
   Für alle Profile ≠ `developer-qemu` werden Autopilot-Symlink, -Unit, -Script und der `090`-Hook entfernt (dev-agent zusätzlich bei `standard`).

3. **Regressionssperre in beiden Validatoren:**
   - `validate-rescue-iso-squashfs.sh`: non-developer-qemu ISO → Autopilot-Script/-Symlink **verboten** (exit 12).
   - `validate-controlled-live-build-tree.sh`: non-developer-qemu Build-Tree → Autopilot-Artefakte **verboten** (exit 1); developer-qemu → Guard-Pflicht.

## Verifikation (ohne sudo)

- `bash -n` aller drei Scripts: OK.
- `pytest` (19 Tests, qemu-autopilot/profile/preflight): **passed**.
- Neue Sperre gegen **aktuelle (fehlerhafte)** ISO: `SYSTEMD_ENABLE_GAP … hangs boot on hardware` → **exit 12** (Defekt wird jetzt gefangen).
- Leak-Check gegen **bereinigten** Build-Tree: `OK: no developer-qemu autopilot leak`.
- Version-Konsistenz: `scope=workspace ok=True` (1.7.18.1 / semver 1.7.18).

## Operator-Anweisung (Phase 0 / TTY mit sudo erforderlich)

```bash
cd /home/volker/piinstaller
# 1) Sauberen Build-Tree erzwingen (entfernt stale binary.hybrid.iso + chroot)
sudo scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
# 2) Prepare (purged jetzt developer-qemu-Leak) + Validate + Build (standard)
sudo SETUPHELFER_RESCUE_BUILD_PROFILE=standard \
  scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
# 3) ISO-squashfs-Validierung MUSS jetzt grün sein:
bash scripts/rescue-live/validate-rescue-iso-squashfs.sh \
  build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
#    erwartet u.a.: "OK: no developer-qemu autopilot leak in standard squashfs"
# 4) USB schreiben + verifizieren (siehe R8B-Anweisung), dann MSI-Boot-Test.
```

**Erwartung nach Rebuild:** Kein Autopilot-Service mehr aktiv → `multi-user.target` blockiert nicht → `start-assistant`/TUI-Menü erreichbar; R6 `boot_marker.md` wird geschrieben.
