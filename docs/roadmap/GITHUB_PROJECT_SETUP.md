# GitHub Project – Setup

**Projektname:** Setuphelfer – Produktionsreife & Testmatrix

## Views

| View | Layout | Zweck |
|------|--------|--------|
| Ampel Board | Board | Grün / Gelb / Rot / Schwarz |
| Hardware Testmatrix | Table | Geräte, Medien, Evidence |
| Recovery Gate | Table | Backup / Verify / Restore |
| Rescue Stick | Board / Table | Read-only Bootstick |
| Release Gate | Table | UG- / Produktionsstart |
| Blocker | Board | akute Hindernisse |

## Felder (Single Select / Text)

| Feld | Typ | Werte bzw. Hinweis |
|------|-----|---------------------|
| Ampel | Single select | Grün, Gelb, Rot, Schwarz |
| Bereich | Single select | Backup, Verify, Restore, Hardware, Rescue, Website, Affiliate, Monolith, Release |
| Priorität | Single select | P0, P1, P2, P3 |
| Risiko | Single select | Datenverlust, Bootfehler, Security, UX, Recht, Monetarisierung, Wartbarkeit |
| Teststatus | Single select | Offen, Unit grün, VM grün, Hardware grün, Regression offen, Blockiert |
| Evidence | Text | Pfad z. B. `docs/evidence/...` oder Link |
| Version | Text | z. B. `1.5.0.0` |
| Abnahme | Single select | Offen, Review, Abgenommen, Blockiert |

## Anlage

1. In GitHub unter **Projects** neues Project (Table/Board) anlegen.
2. Obige Felder als **custom fields** definieren.
3. Issues aus `docs/testing/*.md` Matrizen und `docs/roadmap/STATUS_MATRIX.md` ableiten.
4. Template **Setuphelfer Test-/Roadmap-Punkt** (`.github/ISSUE_TEMPLATE/setuphelfer_test_item.md`) nutzen.
