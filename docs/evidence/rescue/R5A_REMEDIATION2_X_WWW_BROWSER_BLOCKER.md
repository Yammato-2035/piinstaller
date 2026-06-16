# R.5A Remediation-2 — x-www-browser Blocker

**Datum:** 2026-06-13  
**Run-ID:** `r5a_rebuild_clean_20260613_161740`

## Blocker

| Feld | Wert |
|------|------|
| **LB_EXIT** | **123** |
| **Phase** | `lb_chroot_install-packages install` |
| **Profil** | `standard` |

## Fehlermeldung (Build-Log)

```
Package x-www-browser is not available, but is referred to by another package.
This may mean that the package is missing, has been obsoleted, or
is only available from another source

E: Package 'x-www-browser' has no installation candidate
LB_EXIT=123
```

## Ursache

`setuphelfer.list.chroot` Zeile 47 enthielt `x-www-browser`.

## Bewertung

| Aspekt | Ergebnis |
|--------|----------|
| Pakettyp | **invalid** — virtuelles Alternatives-Ziel, kein installierbares Debian-Paket |
| Alternativname | keiner in bookworm-Archive als eigenständiges `.deb` |
| Browser-Bedarf | durch **`chromium`** abgedeckt |

## Entscheidung

**`x-www-browser` aus package-list entfernen.** Runtime-Fallback in Kiosk-Skripten via `command -v x-www-browser` erlaubt (alternatives-Symlink nach Installation von chromium), aber **nicht** als apt-Paket listen.
