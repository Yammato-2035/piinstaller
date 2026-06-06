# RESCUE_ISO_PARENT_ARCHIVE_AREAS_FAILURE

**Datum:** 2026-06-06  
**HEAD:** `2a36003` · **Version:** `1.7.4.3`

## Fehler

```text
E: Unable to locate package firmware-iwlwifi
E: Unable to locate package firmware-intel-sound
LB_EXIT=123
```

Log:

```text
I: Checking component main on http://ftp.debian.org/debian...
Get:9 http://security.debian.org bookworm-security/non-free-firmware amd64 Packages
```

## Ist-Zustand (chroot)

```text
deb http://ftp.debian.org/debian/ bookworm main
deb http://security.debian.org/ bookworm-security main contrib non-free-firmware
```

Security hatte `non-free-firmware`, Parent-Mirror **nur `main`**.

## Root Cause

| Ursache | Detail |
|---------|--------|
| Unquoted `archive-areas` | Shell übergab nur `main` an `lb config` |
| Fehlende Parent-Listen | Keine `config/archives/debian.list.chroot` |
| Fehlende `parent-archive-areas` | Parent-Mirror blieb main-only |
| Stale chroot | Alte `sources.list` überlebte Rebuild |

Fix `2a36003` (Security + unquoted archive-areas String) **unzureichend**.

## Klassifikation

```json
{
  "failure_code": "RESCUE-ISO-PARENT-ARCHIVE-AREAS-001",
  "lb_exit": 123,
  "root_cause": "bookworm main repository lacks non-free-firmware in effective chroot apt sources",
  "iso_created": false,
  "usb_write_allowed": false,
  "windows_inspect_allowed": false
}
```

Stick bleibt alter Stand (`09b9482a…`). Kein USB-Write in diesem Prompt.
