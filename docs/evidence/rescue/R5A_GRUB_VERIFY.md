# R.5A — GRUB-Verifikation

## Post-Build (neue ISO)

**Nicht ausführbar** — kein neuer `lb build` in R.5A Agent-Session.

## Staging-Preflight (weiterhin gültig)

`verify-rescue-grub-theme.sh` auf Build-Tree:

| Prüfung | Ergebnis |
|---------|----------|
| theme.txt | OK |
| PNG Assets | OK |
| grub.cfg | WARN (pre-build) |
| ISOLINUX | OK |

## Nach Operator-Build

```bash
./scripts/rescue-live/verify-rescue-grub-theme.sh
# Erwartung: Exit 0 wenn grub.cfg Theme referenziert
```

## Ampel (vorläufig)

| Aspekt | Ampel |
|--------|-------|
| GRUB Theme Assets | **green** |
| GRUB grub.cfg fertig | **yellow** |
