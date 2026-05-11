# Hardware Profile Schema (DIAG-1.1)

## Zweck

System-/Hardwarekontexte standardisieren, damit Diagnosen reproduzierbar vergleichbar bleiben.

## Struktur

`SystemProfile`:

- `id`
- `platform_class`: `raspberry_pi`, `linux_pc`, `linux_laptop`, `vm`, `rescue_media`
- optional: `hostname`, `manufacturer`, `model`
- `cpu_model`, `cpu_arch`, `core_count`, `ram_total_mb`
- `os_name`, `os_version`, `kernel_version`
- `boot_mode`: `sd`, `usb`, `nvme`, `mixed`, `unknown`
- `filesystem_root`, `filesystem_backup_target`
- `storage_devices[]`
- optional: `network_summary`

`StorageDevice`:

- `name`
- `type`: `sd`, `usb`, `nvme`, `sata`, `loop`
- `size_gb`
- `filesystem`
- `mountpoint`
- `removable`
- `encrypted`
- optional: `health_info`

## Validierungsregeln

- Keine negativen Groessen-/RAM-/Core-Werte.
- Nur definierte Platform-/Device-/Boot-Typen.
- Keine persoenlichen Daten ohne Diagnosemehrwert.

## Ablage

- `data/diagnostics/profiles/*.json`
