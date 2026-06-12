# KB: System Status Facade

Nach F.4 (DCC) folgt G.1: kanonische **System Status Facade**.

## Was macht G.1?

- Neues Modul `core/system_status_facade.py`
- Contract + Delegation — **keine Route verschoben**
- Ampel-Logik (`/api/system/status`) über Legacy-Adapter aus `app._compute_system_status`
- Keine Netzwerkdiagnostik (kommt in G.2)

## Nächste Schritte

1. **G.1b** — `/api/system/status` auf Facade migrieren
2. **G.2** — Network Info Facade für `/api/status` network block

Vollständig: [SYSTEM_STATUS_FACADE_G1.md](../../architecture/SYSTEM_STATUS_FACADE_G1.md)
