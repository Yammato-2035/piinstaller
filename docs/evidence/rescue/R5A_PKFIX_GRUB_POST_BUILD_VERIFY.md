# R.5A PKFix — GRUB Post-Build Verify

**ISO:** `binary.hybrid.iso`  
**Build-Tree-Skript:** `verify-rescue-grub-theme.sh` (Exit 5, 1 Warnung pre-ISO)

## Build-Tree Verify (`verify-rescue-grub-theme.sh`)

```
OK: grub theme.txt
OK: grub theme PNG (setuphelfer-boot-menu-de.png)
OK: ISOLINUX fallback config
WARN: no grub.cfg in build tree yet (pre-lb build)
fail_count=0 warn_count=1
```

## ISO Read-Only Checks

| Check | Status | Detail |
|-------|--------|--------|
| `/boot/grub/grub.cfg` | **FOUND** | menuentry „Setuphelfer Rescue Live“ |
| `set theme=` / theme-Einbindung | **MISSING** | kein `set theme=` in grub.cfg |
| `/boot/grub/themes/setuphelfer/theme.txt` | **FOUND** | |
| setuphelfer PNG | **FOUND** | `setuphelfer-boot-menu-de.png` |
| `/EFI/BOOT/BOOTX64.EFI` | **FOUND** | UEFI validate Exit 0 |
| ISOLINUX fallback | **FOUND** | `/isolinux/isolinux.cfg` |

## UEFI Validator

```
validate-rescue-iso-uefi-boot.sh → Exit 0
BOOTX64=true EFI_ELTORITO=true HYBRID=true
```

## Bewertung

| Bereich | Ampel |
|---------|-------|
| Theme-Assets in ISO | **green** |
| grub.cfg theme reference | **yellow** (Assets da, `set theme=` fehlt) |
| UEFI BOOTX64 | **green** |
| ISOLINUX | **green** |
| **Gesamt GRUB** | **yellow** (mindestanforderung erfüllt, nicht optimal) |

Bekanntes Rest-Risiko: Grafisches GRUB-Theme wird ohne `set theme=` möglicherweise nicht aktiv — Boot funktionsfähig, Branding suboptimal.
