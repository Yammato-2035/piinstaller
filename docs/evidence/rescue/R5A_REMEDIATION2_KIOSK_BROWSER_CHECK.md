# R.5A Remediation-2 — Kiosk Browser Check

**Datum:** 2026-06-13

## Geprüfte Skripte

- `scripts/rescue-live/image/setuphelfer-rescue-kiosk-start`
- `scripts/rescue-live/image/setuphelfer-rescue-kiosk-health`
- `scripts/rescue-live/image/setuphelfer-rescue-ui-launch` (Referenz)

## Vorher

Browser-Suche bereits **chromium-first**:

```
chromium → chromium-browser → firefox-esr → firefox
```

Kein Paket-Install für `x-www-browser`; Skripte erwarteten das Paket **nicht**.

## Anpassung (Runtime-Fallback)

Reihenfolge erweitert um alternatives-Symlink **ohne** apt-Paket:

```
1. chromium
2. chromium-browser
3. firefox-esr
4. firefox
5. x-www-browser   ← nur command -v / which, falls alternatives existiert
```

## Bewertung

| Check | Ergebnis |
|-------|----------|
| chromium-first | **ja** |
| x-www-browser als Paket | **nein** (entfernt aus list.chroot) |
| x-www-browser Runtime-Fallback | **ja** (optional, nach firefox) |
| Skript-Korrektur nötig war | minimal (Fallback ergänzt) |

**Kiosk Browser-Fallback chromium-first: ja**
