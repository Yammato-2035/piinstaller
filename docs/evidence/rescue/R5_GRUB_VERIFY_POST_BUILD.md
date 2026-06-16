# R.5 — GRUB-Verifikation nach Build

## Status

**Kein Post-Build-`lb build` in R.5** (Gate A fehlt). Verifikation auf **Staging-Tree** + **stale ISO**:

## Staging (`verify-rescue-grub-theme.sh`)

| Prüfung | Ergebnis |
|---------|----------|
| theme.txt + PNG im Binary-Staging | OK |
| grub.cfg im Build-Tree | **fehlt** (pre-lb) |
| ISOLINUX | OK |

## Stale ISO (2026-06-07)

Grafisches GRUB in fertiger `grub.cfg` der **alten** ISO nicht separat in dieser Phase extrahiert — erwartet nach neuem Build.

## Bewertung (vorläufig)

| Aspekt | Ampel |
|--------|-------|
| Assets gestaged | **green** |
| grub.cfg Theme-Eintrag (fertig) | **yellow** — erst nach lb build prüfbar |
| Kiosk-relevante GRUB-Menüeinträge | **gray** — Snippet in `setuphelfer-rescue-grub-menu-snippet.cfg` vorhanden |

## Nach Gate A + Build

`verify-rescue-grub-theme.sh` erneut — Exit 0 erwartet wenn `grub.cfg` Theme referenziert.
