# Rescue Build — Monolith / Boundary Gate

**Datum:** 2026-05-24  
**Git HEAD:** `d3d8029`  
**Gesamtstatus:** **review_required** (ISO-Prep möglich, kein Blocker für Temp-Bundle)

## Prüfmatrix

| # | Frage | Ergebnis | Status |
|---|-------|----------|--------|
| 1 | Muss Rescue-Bundle `backend/app.py` vollständig mitnehmen? | **Ja** — FastAPI-Einstieg; kein schlanker Rescue-only-Server ohne größeren Refactor | review_required |
| 2 | Harte Imports auf Dev-/Deploy-/Host-only? | Deploy-Router optional geladen; `core/install_paths` löst `/opt/setuphelfer` zur Laufzeit | review_required |
| 3 | Pfade falsch im Live-System? | `install_paths` + cwd-abhängig; Temp-Bundle setzt `SETUPHELFER_RESCUE_ROOT` | review_required |
| 4 | Abhängigkeiten auf `/opt`, `/home`, Workspace? | `app.py` enthält Host-Beispiele (`/home/*`, `/opt/volumio`); nicht alle Rescue-relevant | review_required |
| 5 | Versteckte Schreibpfade? | Backup/Deploy/Partition-Routen vorhanden; Safety-Gates + write_guard in Partitions-Core | review_required |
| 6 | API-Routen im Rescue-Modus deaktivieren? | **Noch nicht** — kein `rescue_mode_policy` implementiert (Phase 3 nicht nötig für Prep) | review_required |
| 7 | Legacy-/piinstaller-Branding? | Branding-Guard in Emulation; Bundle-Scan ohne `pi-installer` in Pfadnamen (cache ausgeschlossen) | ok |
| 8 | Frontend gefährliche Aktionen? | Volle SPA; localhost-only reduziert LAN-Risiko; Write weiterhin backend-gated | review_required |
| 9 | Safety-Gates zwingend aktiv? | **Ja** — nicht lockern; Partitions hardstop, emulation `write_defaults_blocked` | ok |
| 10 | Monolith vor ISO extrahieren? | **Später** — `app.py` ~17k LOC, `deploy/routes.py` ~5k; Temp-Bundle nutzt volles Backend + venv | review_required |

## Größenordnung

| Komponente | LOC (ca.) |
|------------|-----------|
| `backend/app.py` | 17 203 |
| `backend/deploy/routes.py` | 5 003 |
| `backend/core/` | 36 Module |

## Entscheidung Phase 3

**Keine Monolith-Entkopplung** in diesem Auftrag — Gate ist **review_required**, nicht **blocked**. Temp-Runtime-Bundle + Controlled ISO Prep Gate reichen für nächsten Schritt.

## Risiken (dokumentiert)

- Volles Backend auf Live-Medium: Deploy-/Backup-Endpunkte theoretisch erreichbar auf localhost — Operator darf nur local-only starten.
- Host-Pfad-Strings in `app.py` für Nicht-Rescue-Features — kein Laufzeitfehler auf Live, aber Bundle-Größe hoch (~2777 Dateien mit venv).

## Referenzen

- `RESCUE_TEMP_RUNTIME_BUNDLE_PREVIEW.md`
- `RESCUE_STICK_CONTROLLED_ISO_PREPARATION_GATE.md`
