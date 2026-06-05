# RESCUE ISO UEFI Patch — Failure Triage (xorriso)

**Status:** `patch_script_fixed_awaiting_operator_run`  
**Datum:** 2026-06-05

## Symptom (Operator)

```text
xorriso : WARNING : Boot image load size exceeds 65535 blocks of 512 bytes.
libisofs: FAILURE : Cannot open data file for appended partition
xorriso : FAILURE : Failed to prepare session write run
RESCUE-UEFI-PATCH-XORRISO-001: xorriso mkisofs failed
```

## Root Cause (zwei unabhängige Fehler)

### 1) `-append_partition` mit relativem Pfad (primär)

| Feld | Fehlerhaft (alt) | Korrekt (neu) |
|------|------------------|---------------|
| `-e` | `boot/grub/efi.img` | `boot/grub/efi.img` (ISO-intern, relativ zu `$STAGING`) |
| `-append_partition` | `boot/grub/efi.img` (relativ zu CWD) | **`$(readlink -f "$WORK/efi.img")`** absoluter Host-Pfad |

`libisofs` öffnet die Append-Partition-Datei **auf dem Host**, nicht im ISO-Staging-Baum. Relativer Pfad → *Cannot open data file for appended partition*.

### 2) ESP zu groß für El-Torito `-e` (sekundär / Warnung)

| `mkfs.vfat -C count` | Dateigröße (Debian bookworm) | 512-Byte-Blöcke |
|----------------------|------------------------------|-----------------|
| 32768 | 32 MiB | **65536** (> 65535 Limit) |
| 16384 | 16 MiB | 32768 (OK) |

Warnung *Boot image load size exceeds 65535 blocks* entstand, weil `-C 32768` hier **32 MiB** erzeugt (count × 1024), nicht 16 MiB.

## Fix (Workspace `fc8223f` → Patch-Lauf)

1. ESP auf Host: `$WORK/efi.img` via `mkfs.vfat -C … 16384`
2. Kopie nach `$STAGING/boot/grub/efi.img` für `-e`
3. `-append_partition 2 0xef "$ESP_IMG_ABS"` mit absolutem Pfad
4. Debug-Zeilen `UEFI_PATCH_DEBUG:*` vor xorriso
5. Agent-Verifikation: Patch nach `/tmp/…` + Validator **Exit 0** (ohne sudo, ohne Canonical-ISO zu überschreiben)

## ISO-Baseline (canonical, unverändert)

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| SHA256 | `d008fb5ed4fbc0836a08d489434930bbbe3141b9b164b6a101a6eb438d11f94a` |
| UEFI Validator | Exit **34** (isolinux_only) |

## Agent-Verifikation (Test-ISO, nicht canonical)

| Feld | Wert |
|------|------|
| Pfad | `/tmp/setuphelfer-rescue-uefi-patch-test2.iso` |
| SHA256 | `1d8955dcbe532a0cc75970b381614f091bde3538eeb6a00d85a3b57d6edb3a63` |
| Validator | Exit **0** |
| BOOTX64.EFI | ja |
| boot/grub/efi.img | ja |
| EFI + BIOS El Torito | ja |

## Nicht ausgeführt

- Kein `--in-place` auf canonical ISO (root-owned, Operator sudo)
- Kein USB-Write
- Kein Deploy / Backend-Restart

**Next Prompt:** `RESCUE_ISO_UEFI_PATCH_OPERATOR_RUN`
