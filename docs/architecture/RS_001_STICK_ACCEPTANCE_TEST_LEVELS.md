# RS-001 Stick Acceptance Test Levels

**Version:** 1.7.11.0  
**Zweck:** Hardware-Retest erst freigeben, wenn der Stick vorgelagerte Contracts besteht.

---

## Level 0 — Repo / Evidence Gate

- Workspace-HEAD dokumentiert
- Kein Fake-Green in Evidence
- Runtime-Gate optional (dev-dashboard 404 nicht blockierend für statische Acceptance)

**Tool:** manuelle Gate-Skripte, `git status`

---

## Level 1 — FAT32-ESP Layout + Hash Gate

**Prüft (read-only):**

- Target `/dev/sdb`, Partition vfat `SETUPHELFER`, GPT `SETUPHELFER_RESCUE`
- Pflichtdateien: `EFI/BOOT/BOOTX64.EFI`, `boot/grub/grub.cfg`, `live/*`, `setuphelfer/rescue/boot-branding.txt`
- `grub.cfg`: Menü „Setuphelfer Rettung starten“, root search, kernel/initrd-Pfade
- SHA256 `live/filesystem.squashfs` = erwarteter Hash

**Tool:** `scripts/rescue-live/check-rs001-stick-acceptance.sh`

**Exit bei Fehler:** 11 (layout), 12 (hash)

---

## Level 2 — SquashFS Content Contract

**Prüft (read-only via `unsquashfs`):**

- React Rescue Shell, `rescue.html`, Launcher, Fallback-TUI
- Offline-first: network boot-skip, telemetry skipped, wait-online neutralized
- Kein network/telemetry Boot-Autostart
- Version im SquashFS

**Exit bei Fehler:** 13

---

## Level 3 — Launcher / Fallback-TUI / Netzwerk Contract

**Prüft im SquashFS (ausführbarer Contract):**

- Launcher schreibt `rescue-ui-status.json`, `review_required` bei fehlendem Browser
- Fallback-TUI: Setuphelfer-Rettungsstick, Status-Kurzfassung, sicheres Netzwerk
- Netzwerk: `set +e`, `return_to_menu`, non-fatal interactive exit, TTY-Override

**Zusätzlich Workspace:** `test-rescue-ui-launcher-contract.sh`, `test-fallback-tui-menu-contract.sh`

**Exit bei Fehler:** 15–17, 20 (review_required)

---

## Level 4 — GRUB Branding Contract

**Prüft auf ESP:**

- `boot/grub/themes/setuphelfer/theme.txt` + Background-PNG
- `grub.cfg`: `set theme=`, `insmod gfxterm/png`
- BOOTX64 gfx-Module in evidence.json

**Exit bei Fehler:** 14, 20 (review_required)

---

## Level 5 — Optional QEMU Boot-Smoke

**Optional:** `scripts/rescue-live/run-rs001-qemu-menu-smoke.sh`

- Kein USB-Write, keine Zielplatte, `-snapshot`
- Serial-Log: GRUB/Kernel/Setuphelfer, keine failed Units vor Menü

**Nicht zwingend** für Hardware-Freigabe; hilfreich vor Level 6.

---

## Level 6 — Hardware-Retest

Erst sinnvoll wenn **Level 1–4 grün** (`acceptance_status=ok`).

**RS-001 grün** nur nach erfolgreichem Level 6 mit nutzbarem Menü.

---

## Regeln

| Regel | Wert |
|-------|------|
| Hardware-Retest vor Level 1–4 grün | **verboten** (nur review_required) |
| QEMU fehlt | nicht fatal |
| RS-001 ohne Hardware-Retest | **yellow** |
| Stick Acceptance `ok` | `hardware_retest_allowed=true` |

---

## JSON-Output

Siehe `check-rs001-stick-acceptance.sh` — Felder `acceptance_status`, `levels`, `hardware_retest_allowed`, `rs001_status`.
