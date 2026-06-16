# R.5A Remediation-2 — Validator Update

**Datum:** 2026-06-13

## `validate-controlled-live-build-tree.sh`

Neue Prüfungen nach `dbus`:

```bash
# x-www-browser verboten
grep -qx 'x-www-browser' → fail_invalid_package (Exit 15)

# Browser-Pflicht
chromium ODER firefox-esr muss gelistet sein

# Display-Stack Pflicht
xserver-xorg, xinit, openbox, dbus-x11, x11-xserver-utils
```

Neue Fail-Funktion: `fail_invalid_package` → `RESCUE-ISO-INVALID-PACKAGE-001`

## `validate-live-build-dpkg-preflight.sh`

`x-www-browser` in `FORBIDDEN_PACKAGES` ergänzt (Exit 13 bei Treffer).

## Verifikation

Nach Fix: Validator Exit **0** — `x-www-browser` nicht mehr in list.chroot, `chromium` vorhanden.
