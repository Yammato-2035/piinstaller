# QEMU Serial Capture and Bootloader Output — Fix Result

**HEAD:** `2091262` (vor Fix-Commit)
**Repository:** PUBLIC — Push blocked

## Geänderte Komponenten

| Datei | Änderung |
|-------|----------|
| `scripts/rescue-live/run-qemu-developer-iso-smoke.sh` | Default `chardev` + `isa-serial`; `prepare_serial_log`; `--serial-backend`; Meta-JSON |
| `scripts/rescue-live/prepare-controlled-live-build-tree.sh` | `write_developer_qemu_isolinux_serial_config`; GRUB binary hook |
| `scripts/tests/test_qemu_serial_capture_args_v1.sh` | neu |
| `scripts/tests/test_rescue_bootloader_serial_config_v1.sh` | neu |
| `docs/architecture/QEMU_SERIAL_CAPTURE_AND_BOOTLOADER_OUTPUT_CONTRACT.md` | neu |

## Sollzustand (Checkliste)

| # | Kriterium | Status |
|---|-----------|--------|
| 1 | Default chardev+isa-serial | **yes** |
| 2 | Legacy `-serial file` nur per Flag | **yes** |
| 3 | Serial-Log vor Start schreibbar geprüft | **yes** |
| 4 | ISOLINUX SERIAL + TIMEOUT + DEFAULT live- | **yes** (prepare, developer-qemu) |
| 5 | GRUB serial terminal vorbereitet | **yes** (binary hook) |
| 6 | Kernel cmdline tty0+ttyS0 | **unverändert grün** |
| 7 | quiet/splash Developer-Append | **nein** |

## Tests (statisch)

```bash
bash -n scripts/rescue-live/run-qemu-developer-iso-smoke.sh
bash -n scripts/rescue-live/prepare-controlled-live-build-tree.sh
scripts/tests/test_qemu_serial_capture_args_v1.sh
scripts/tests/test_rescue_bootloader_serial_config_v1.sh
scripts/tests/test_rescue_developer_serial_cmdline_v1.sh
```

## Nicht in diesem Auftrag

- Kein ISO-Rebuild
- Kein QEMU-Smoke
- Kein USB/Backup/Restore/apt/Push

## Nächste Schritte (Operator)

1. `export SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu`
2. `./scripts/rescue-live/prepare-controlled-live-build-tree.sh`
3. Controlled ISO rebuild (sudo/Operator-Terminal)
4. Statische ISO-Validierung
5. **Genau ein** QEMU-Serial-Smoke-Retry
