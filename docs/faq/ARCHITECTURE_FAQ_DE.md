# Architektur-FAQ — Core Facades (DE)

Kurzantworten zu Storage/Mount/Safety-Facades (Phase A.1 + Caller-Migration A.2–A.4). Keine Produktwerbung.

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

## Was wurde in A.2–A.4 migriert?

`preflight/backup.py`, `backup_engine.py` und `restore_engine.py` importieren Safety nur noch über `core.safety_facade`. Fehlercodes und Verhalten sind unverändert (Delegation).

## Warum wird `app.py` nicht sofort zerlegt?

~18k Zeilen, ~213 Routen — Router-Extraktion erfordert eigene Phase B mit OpenAPI-Parität. Safety-Migration der Engines war isolierbar und risikoarm.

## Warum bleibt der Boundary Guard teilweise warn-only?

`app.py`, Deploy-Runner und Storage-Legacy sind noch nicht migriert. Verschärfte Prüfung gilt bereits für die drei migrierten Safety-Caller.

## Ändert sich das Backup- oder Restore-Verhalten?

**Nein** — gleiche `safe_device`/`write_guard`-Logik, nur zentraler Importpfad. Keine neuen Zielpfade, keine abgeschwächten Gates.

## Warum ist das sicherer?

Weniger verstreute Imports → weniger Risiko, dass neue Module eigene Safety-Logik bauen. Boundary Guard erkennt Rückfälle in migrierten Dateien.

## Was wurde in B.1 migriert?

blkid/Storage-Erkennung in `backup_target_auto_prepare` und `inspect/collector` läuft über `storage_facade`. `partition_storage_facade` nutzt `safety_facade` statt direktem `write_guard`.

## Was ist die Deploy Runner Registry (C.1)?

Statisches Inventar und Metadaten für **115** `runner_*.py` unter `backend/deploy/`. Modul: `runner_registry.py`. **Keine** Runner-Ausführung, **kein** Refactoring der Runner selbst.

## Was ist der Runner Result Contract (C.2)?

Einheitliches Ergebnisschema (`RunnerResult`) mit 6 Statuswerten, `warnings`/`errors`, `evidence_paths` und `no_execution_performed`. Modul: `runner_result_contract.py`. Legacy-Dicts werden per `normalize_legacy_runner_result` abbildbar — Runner selbst unverändert.

## Warum werden Runner nicht sofort refaktoriert?

Größtes Risiko-Cluster (~37k Zeilen). C.1 + C.2 liefern Metadaten und Result-Contract. C.3–C.5: API Facade, Risk Gate, schrittweise Migration.

## Was ist die Deploy Runner API Facade (C.3)?

Read-only Schicht `runner_api_facade.py` + **5 GET-Routen** unter `/api/deploy/runners/*`. Listet Registry/Contract — **keine** Runner-Ausführung. Die 112 direkten Runner-Imports in `routes.py` bleiben vorerst.

## Was ist das Deploy Runner Risk Gate (C.4)?

`runner_risk_gate.py` wertet `risk_level`, `execution_policy` und optional Operator-Kontext aus. **`allowed_to_execute` bleibt immer false** — nur Planungsentscheidungen für C.5.

## Nächster Schritt?

Phase **C.5** schrittweise Runner-Migration.

## Weiterlesen

- `docs/knowledge-base/architecture/CORE_FACADES.md`
- `docs/architecture/STORAGE_DISCOVERY_INVENTORY.md`
- `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4.md`
- `docs/architecture/DEPLOY_RUNNER_REGISTRY.md`
- `docs/architecture/DEPLOY_RUNNER_RESULT_CONTRACT.md`
- `docs/architecture/DEPLOY_RUNNER_API_FACADE.md`
- `docs/architecture/DEPLOY_RUNNER_RISK_GATE.md`
