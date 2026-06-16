# R.5A Remediation-2 — Tree Prepared

**Datum:** 2026-06-13

## Prepare

```bash
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
```

```
OK: bundle copied to includes.chroot/opt/setuphelfer-rescue (2938 files ref)
OK: rescue_build_profile=standard
```

## x-www-browser Check

```bash
grep -n "x-www-browser" .../setuphelfer.list.chroot || true
```

**Ergebnis:** kein Treffer (`NO_MATCH_OK`)

## Zeilen

**47** (vorher 48)

## R.4 + Netzwerk-Pakete (grep)

```
chromium
xserver-xorg
xinit
openbox
dbus-x11
x11-xserver-utils
unclutter
fonts-dejavu
fonts-noto
wireless-tools
iw
wpasupplicant
network-manager
```

Alle vorhanden.
