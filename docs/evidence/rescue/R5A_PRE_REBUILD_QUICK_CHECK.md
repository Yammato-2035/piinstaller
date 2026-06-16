# R.5A — Pre-Rebuild Quick Check

**HEAD:** `57e30d9`  
**Datum:** 2026-06-13

## Package-List

| Check | Ergebnis |
|-------|----------|
| Zeilen | **48** |
| chromium | **ja** |
| xserver-xorg | **ja** |
| openbox | **ja** |
| xinit | **ja** |
| dbus-x11 | **ja** |
| unclutter | **ja** |

## Runtime-Bundle (`includes.chroot/opt/setuphelfer-rescue/`)

| Check | Ergebnis |
|-------|----------|
| MANIFEST `source_head` | **57e30d9** |
| rescue_persistence.py | **ja** |
| rescue_test_matrix.py | **ja** |
| rescue_telemetry_spool.py | **ja** |
| rescue_evidence_bundle.py | **ja** |
| rescue.html | **ja** (`usr/share/setuphelfer/rescue/ui/rescue.html`) |

## Gesamt

**Package/Bundle Quick Check: grün** — Remediation-Stand intakt.

**Rebuild-Blocker:** nur noch Permission (`cache/` root-owned), nicht Inhalt.
