# Cockpit Roadmap UX — Uncommitted Review

**Datum:** 2026-05-27  
**Dateien:** `ExternalDevelopmentControlCenter.tsx`, `RoadmapDrawer.tsx`

## Bewertung

| Kriterium | Ergebnis |
|-----------|----------|
| Zielbezogen | Ja — nur Sichtbarkeit/Navigation |
| Statuslogik geändert | **Nein** |
| Fake-Green | **Nein** |
| Rote/gelbe Gates versteckt | **Nein** — Panels unverändert |
| i18n | Nutzt bestehende Keys `devDashboard.nav.roadmap` |

## Änderungen

1. **Roadmap + ReadyStable** direkt unter Alerts, **vor** Rescue/Backup-Panels (weniger Scrollen).
2. **Button „Roadmap“** in der Kopfzeile scrollt zu `#dev-dashboard-roadmap-panel`.
3. **RoadmapDrawer:** `id` für Anker + Datenquellen-Banner (bereits committed in 5786eb3 teilweise).

## Empfehlung

**Committen** mit Roadmap-Completion — risikoarm, verbessert Cockpit-Sichtbarkeit ohne Gate-Schwächung.
