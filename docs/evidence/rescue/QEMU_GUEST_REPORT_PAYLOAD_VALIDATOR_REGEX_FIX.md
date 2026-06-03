# QEMU Guest Report Payload — Validator Regex Fix

**Status:** `ok`

## Änderung

`validate-rescue-iso-squashfs.sh`: Akzeptiert `-m devserver_agent.cli` auch in Python-`subprocess`-Listen (nicht nur Shell `python3 -m ...`).

## Verifikation

- Bestehendes ISO (Squashfs mit subprocess-Aufruf): **validate_iso_exit=0** nach Fix
- Autopilot-Profil enthält `devserver_agent.cli` + PYTHONPATH + Host-Header

## Tests

`test_devserver_agent_guest_report_payload_fix_v1::test_validator_accepts_subprocess_cli_pattern`
