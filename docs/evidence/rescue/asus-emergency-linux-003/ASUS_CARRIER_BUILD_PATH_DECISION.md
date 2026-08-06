# ASUS_CARRIER_BUILD_PATH_DECISION

Stand: 2026-08-06  
Branch: `pi-rs-asus-emergency-linux-telemetry-003`  
Version: Projekt **1.10.2.0**, Payload **1.10.0.17**

## Entscheidung

**`controlled_iso_required`**

Primärpfad: **CONTROLLED ISO BUILD**  
Repack: nur dokumentierter Fallback, **nicht** automatisch.

## Begründung

Prüfkriterien für Repack-Zulässigkeit:

| # | Kriterium | Nachweis im Worktree |
|---|-----------|----------------------|
| 1 | verifiziertes Basis-ISO vorhanden | **nein** |
| 2 | Kernel passt exakt zum neuen Payload | **nicht prüfbar** (kein Artefakt) |
| 3 | initramfs unverändert ausreichend | **unklar** — frühe Marker begrenzt, aber Units/Profile neu |
| 4 | Bootloader enthält ASUS-00..05 / RECOVERY | **vorbereitet** in `prepare-controlled-live-build-tree.sh` + GRUB-Snippet — erfordert frischen ISO-Build |
| 5 | systemd-Units korrekt eingebunden | **vorbereitet** (Live-Pfad `/opt/setuphelfer-rescue`, enable in chroot-hook) — erfordert frischen ISO-Build |
| 6 | Version/Commit eindeutig | Projekt **1.10.2.0**, Payload **1.10.0.17**, Track `pi_rs_asus_emergency_linux_telemetry_003` |
| 7 | kein altes Runtimeartefakt | kein ISO/SquashFS im Worktree als Build-Ergebnis |

Artefaktlage und Kernel-/initramfs-Unklarheit → Controlled ISO **required**. Kein Repack-Fallback.

## Offizieller Pfad (bestehend)

1. `scripts/rescue-live/preflight-developer-controlled-iso-build.sh`
2. `scripts/rescue-live/prepare-controlled-live-build-tree.sh`
3. `scripts/rescue-live/run-controlled-iso-build-with-logging.sh`
4. Verify: `validate-rescue-iso-uefi-boot.sh`, `validate-rescue-iso-squashfs.sh`, …
