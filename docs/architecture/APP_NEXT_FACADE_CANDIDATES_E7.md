# APP Next Facade Candidates — Phase E.7

**HEAD:** `72a7c93` · Bewertung vor weiteren Router-Slices (E.8+)

## Kandidaten

| Facade | Zweck | betroffene Routen | Risiko | Bewertung | Empfehlung |
|--------|-------|-------------------|--------|-----------|------------|
| **DCC Status Facade** | Einheitlicher `build_dashboard_status`-Einstieg; Profil-Gate; keine Duplikation in Routern | `GET /api/dev-dashboard/status`, indirekt roadmap/prompt-findings | CRITICAL | **CRITICAL** | Vor Extraktion von Aggregations-GETs; Core-Owner `core.dev_dashboard` |
| **System Status Facade** | Ampel-Engine ohne Route-Duplikation | `GET /api/status`, `GET /api/system/status` | HIGH | **HIGH** | `_compute_system_status` aus Monolith heben; subprocess nur in Facade |
| **Network Info Facade** | IP/Hostname/Interfaces | `GET /api/system/network` | HIGH | **HIGH** | `get_network_info` canonical; Demo-Mode im Facade |
| **Settings Write Facade** | POST settings, UX, SMTP | `POST /api/settings*`, notifications/test | MEDIUM | **MEDIUM** | GET bereits E.2; Write separat |
| **Dev Dashboard Aggregation Facade** | control-center-summary, prompt-findings, cursor-meta-prompt | 3–4 GET | HIGH | **HIGH** | Nach DCC Status Facade |
| **Frontend Status ViewModel Facade** | Ein Response-Shape für UI-Ampeln | Frontend `/api/status` Consumer | MEDIUM | **MEDIUM** | Optional nach System Status Facade; kein neues Parsing |

## Priorität

1. **CRITICAL:** DCC Status Facade — blockiert die meisten verbleibenden DCC-GETs
2. **HIGH:** System Status + Network Info — blockiert Frontend-Systemseite
3. **HIGH:** Dev Dashboard Aggregation — Cockpit/Roadmap-Root
4. **MEDIUM:** Settings Write, Frontend ViewModel

## Module-Reuse

- Keine parallelen lsblk/findmnt/subprocess-Implementierungen in Routern
- Facades als **CANONICAL_MODULE** in `MODULE_CATALOG.md` eintragen **bevor** Implementierung
- Router-Slices delegieren nur an Facade/Core

## Verknüpfung E.8

E.8 (3 Notifications/Backend-Health GETs) **ohne** diese Facades — sicher, da kein `build_dashboard_status`.
