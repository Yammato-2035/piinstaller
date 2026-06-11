# Architektur-FAQ — Core Facades (DE)

Kurzantworten zu Storage/Mount/Safety-Facades (Phase A.1). Keine Produktwerbung.

## Was sind Core Facades?

Drei Module unter `backend/core/`: `storage_facade`, `mount_facade`, `safety_facade`. Sie sind die **kanonische Schnittstelle** für Geräteerkennung, Mount-Pläne und Schreibziel-Prüfungen.

## Warum gibt es sie?

Im Monolith-Audit wurden viele Duplikate gefunden (`lsblk` in `app.py`, `safe_device`, Rescue, Deploy-Runner). Facades verhindern, dass jedes neue Modul dieselbe Logik erneut baut.

## Was wurde in A.1 geändert?

- Öffentliche Contracts (Datentypen + Funktionen)
- Dokumentation und Inventar
- Warn-only Boundary-Check
- Unit-Tests für Contracts

**Nicht** geändert: bestehende APIs, Runtime-Verhalten, Legacy-Imports.

## Darf ich weiterhin `safe_device` direkt importieren?

**Legacy:** ja, bestehender Code bleibt. **Neue Module:** nein — nur Facades (siehe `CORE_FACADE_RULES.md`).

## Führt die Mount-Facade echte Mounts aus?

Nein. `build_readonly_mount_plan` und Validatoren sind **plan-only** / Analyse.

## Welche Safety-Kontexte gibt es?

`live`, `rescue`, `partition_helper`, `cloudserver_future` (`SafetyContext` in `safety_facade.py`).

## Wann blockiert der Boundary-Check?

Aktuell **nur Warnungen** in `check-module-boundaries.sh`. CI-Block ist für eine spätere Phase vorgesehen.

## Nächster Schritt?

Phase A.2: Caller-Migration (z. B. `preflight/backup.py`) — ein Modul pro PR.

## Weiterlesen

- `docs/knowledge-base/architecture/CORE_FACADES.md`
- `docs/architecture/STORAGE_DISCOVERY_INVENTORY.md`
