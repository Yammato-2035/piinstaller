# RESCUE_ISO_NON_FREE_FIRMWARE_COMPONENT_FAILURE

**Datum:** 2026-06-06  
**Prompt:** Operator ISO-Rebuild nach `4f3ca39` / Version `1.7.4.2`

## Ergebnis

**Controlled ISO-Build fehlgeschlagen** — Firmware-Paketnamen korrekt, aber live-build nutzte nur Debian-Komponente **`main`**.

## Fehler (Auszug)

```text
I: Checking component main on http://ftp.debian.org/debian...
E: Unable to locate package firmware-iwlwifi
E: Unable to locate package firmware-intel-sound
LB_EXIT=123
RESCUE-UEFI-001: ISO missing
```

## Klassifikation

| Feld | Wert |
|------|------|
| `failure_code` | **`RESCUE-ISO-FIRMWARE-APT-COMPONENT-001`** |
| `lb_exit` | **123** |
| `root_cause` | live-build archive areas missing `non-free-firmware` |
| `iso_created` | **false** |
| `usb_write_allowed` | **false** |
| `windows_inspect_allowed` | **false** |

## Root Cause

`prepare-controlled-live-build-tree.sh` setzte:

```text
--archive-areas main
```

Debian Bookworm legt `firmware-iwlwifi` und `firmware-intel-sound` in **`non-free-firmware`**.

## Korrektur (Workspace)

```text
--archive-areas main contrib non-free-firmware
```

Validator prüft Archive-Areas + Paketliste gekoppelt.

## Intel-BT-Korrektur

`intel/ibt-17-16-1.sfi` gehört zu **`firmware-iwlwifi`**, nicht zu `firmware-intel-sound`.

## Nächster Schritt

Version **1.7.4.3**, Prepare + Validate, Operator-Rebuild.

## Secrets

Keine Secrets in dieser Datei.
