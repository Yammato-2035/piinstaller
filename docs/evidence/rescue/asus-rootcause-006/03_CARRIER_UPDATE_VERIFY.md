# 03 Carrier Update Verify — PI-RS-ASUS-ROOTCAUSE-TELEMETRY-006

**Status:** `carrier_update_verified`

| Feld | Wert |
|------|------|
| Target | `/dev/sda` Intenso Ultra Line |
| Fingerprint | `ce2e34b7f5ea4e41` |
| Serial | `24111412110212` |
| SquashFS SHA256 | `4629ca614c98a290626508d835c905246739b55f90fe02c393ab93b7641d7866` |
| GRUB boot SHA256 | `15497518ea3632eeb728f4e417ee629b9d69f0e89e0ab884ee25a257d38c9d66` |
| GRUB EFI SHA256 | `15497518ea3632eeb728f4e417ee629b9d69f0e89e0ab884ee25a257d38c9d66` |
| Payload version | `1.10.3.0` |
| SETUP_LOGS preserved | yes |
| Partition rewrite | no |
| FS reformat | no |

## Nächster physischer Schritt

1. Stick sicher auswerfen.
2. **BOOT 1 nur ASUS-TUI-BASELINE** (GRUB default=0).
3. Erwartung: TUI, `console_owner=tui_owned`, kein startx/Xorg/Chromium.
4. Stick zurück → Boot1-Evidence → dann BOOT 2 gleicher Profil.
5. XORG-FORENSIC erst nach 2× TUI-Baseline grün.
