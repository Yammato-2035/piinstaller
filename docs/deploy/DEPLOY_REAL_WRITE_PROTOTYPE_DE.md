# Real-Write-Prototyp (streng limitiert)

## Zweck

Ein erster, absichtlich enger Write-Pfad: sequenzielles Rohschreiben eines **lokalen** Test-Images auf **ein** freigegebenes **removables** USB-/SD-Ziel. Kein Installer, keine Partitionierung, keine Reparaturlogik.

## API

- `POST /api/deploy/write/prototype`
- Es gibt **keinen** allgemeinen Write-Endpunkt; nur dieser Prototyp.

## Umgebung

- `SETUPHELFER_ENABLE_REAL_WRITE=1` muss gesetzt sein. Ohne diese Variable: `DEPLOY_REAL_WRITE_FEATURE_DISABLED`.

## Pflicht-Gates (Kurz)

1. Feature-Flag gesetzt.
2. `readiness_level == test_ready` (über `build_hardware_gate_report` mit denselben Eingaben wie beim Gate).
3. `real_write_guard_result.code == DEPLOY_REAL_WRITE_READY` (Ergebnis des Real-Write-Checks, nicht nur Session-Erstellung).
4. Final Confirmation: `check_final_confirmation_dryrun` liefert `DEPLOY_FINAL_CONFIRMATION_READY`; gebundene `image_path` und `target_device` müssen zum Request passen.
5. Harness-Nachweis: `execute_code`, `sha256_matches`, `single_use_code`, `host_changes_detected` exakt wie in `real_write_guard._validate_harness_proof`.
6. Zielgerät: laut `validate_test_device` u. a. removable, Transport `usb` oder `sdcard`, nicht gemountet, nicht schreibgeschützt, kein System-/Live-/Windows-/Dualboot-/LVM-/RAID-/Loop-Fall (über Inspect + Safety).
7. Image: nur unter erlaubtem Cache-Pfad (`inspect_deploy_image`), gültige Checksumme, Inspect ohne harte Fehler.

## Write-Engine

- Reines Python: `open`, chunked Read/Write (Standard 1 MiB), `os.fsync`.
- Hartes Limit: **512 MiB** Imagegröße; darüber `DEPLOY_REAL_WRITE_IMAGE_TOO_LARGE`.
- Ziel muss ein **Blockdevice** sein (`S_ISBLK`); normale Dateien werden abgelehnt.
- Globaler Mutex: keine parallelen Prototyp-Writes.

## Sofort-Recheck vor `open`

Unmittelbar vor dem Öffnen des Ziels werden u. a. erneut geprüft: Mount/Readonly/Transport/Removable, Fingerprint des `guard_snapshot`, Harness, Final Confirmation, Feature-Flag, Image-Inspect-Konsistenz. Abweichung: Abbruch (`DEPLOY_REAL_WRITE_BLOCKED` oder `DEPLOY_REAL_WRITE_DEVICE_CHANGED`).

## Verify

Nach dem Schreiben: gelesener Bereich wird mit dem Image verglichen; SHA256 über den geschriebenen Umfang. Status: `verified`, `mismatch` oder `failed`. Bei `mismatch`: `DEPLOY_REAL_WRITE_VERIFY_FAILED` (kein Retry).

## Response-Felder

`code`, `prototype_write_id`, `target_device`, `image_path`, `bytes_written`, `chunk_size`, `duration_ms`, `verify`, `warnings`, `errors`.

## Codes (Auszug)

- `DEPLOY_REAL_WRITE_COMPLETED`
- `DEPLOY_REAL_WRITE_VERIFY_FAILED`
- `DEPLOY_REAL_WRITE_BLOCKED`
- `DEPLOY_REAL_WRITE_ABORTED`
- `DEPLOY_REAL_WRITE_DEVICE_CHANGED`
- `DEPLOY_REAL_WRITE_FEATURE_DISABLED`
- `DEPLOY_REAL_WRITE_IMAGE_TOO_LARGE`

## Bewusst nicht enthalten

Kein `dd`, kein Shell/Subprocess, kein `mkfs`/`parted`/Mount/GRUB/chroot/systemctl, keine Netzwerk-Downloads, keine Windows-/Dualboot-Ziele, kein Produktiv-Deploy.
