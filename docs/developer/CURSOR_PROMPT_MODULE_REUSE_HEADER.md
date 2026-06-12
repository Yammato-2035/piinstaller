# Cursor Prompt — Module Reuse Header (DE)

Kopiere diesen Block an den Anfang strukturierter Prompts (Deploy, Rescue, Partitions, DCC, UI):

```markdown
## Module Reuse (Pflicht)

Vor Implementierung lesen und einhalten:
- docs/architecture/MODULE_CATALOG.md
- docs/architecture/FUNCTION_OWNERSHIP_MATRIX.md
- docs/architecture/DO_NOT_DUPLICATE_RULES.md
- docs/architecture/MONOLITH_DECOMPOSITION_ROADMAP.md

Regeln:
- Vorhandene CANONICAL_MODULE/FACADE/CONTRACT/ROUTER verwenden
- Keine parallelen lsblk/blkid/findmnt/Write-Check/Runner-Status-Implementierungen
- Keine Plan-Routen in routes.py wenn Subrouter-Domäne existiert
- Kein Runner ausführen / kein Deploy / kein USB-Write ohne explizite Phase-Freigabe
- Safety-Gates nicht schwächen
- Doku DE+EN, FAQ/KB bei Architekturänderung
- Kein git add -A
- Neues Modul: zuerst MODULE_CATALOG als CANDIDATE
```
