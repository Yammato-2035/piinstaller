# DCC Report Freshness — Frontend Review

**Status:** `frontend_limit_missing` → Fix

| Komponente | Vorher | Nachher |
|------------|--------|---------|
| Dev-Server `latest_findings` | 5 Agent-Uploads, Label „Neueste Berichte“ | Label „Agent-Uploads“ + Hinweis |
| Control-Center Evidence | 20 mtime-Pfade, scroll | `RecentEvidenceFeedPanel` — 5 + Filter |
| Manual command runs | bis 40, scroll | Default 5, „Mehr anzeigen“ |
| Development Dashboard | — | `RecentEvidenceFeedPanel` eingebunden |

**Filter:** Kategorie, Status, Zeitraum, Suche.
