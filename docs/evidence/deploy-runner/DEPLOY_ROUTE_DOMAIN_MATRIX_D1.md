# Deploy Route Domain Matrix (Phase D.1)

**Quelle:** `backend/deploy/routes.py` — statische Analyse 2026-06-10

## Domänen mit Routen

| Domain | Anzahl Routen | ~Zeilen (Handler) | Risiko |
|--------|---------------|-------------------|--------|
| rescue | 84 | ~2100 | **HIGH** |
| evidence | 40 | ~900 | **LOW–MEDIUM** |
| runtime | 26 | ~650 | **CRITICAL** |
| versioning | 23 | ~550 | **MEDIUM–HIGH** |
| rescue_build | 21 | ~500 | **HIGH** |
| governance | 16 | ~400 | **MEDIUM** |
| diagnostics | 7 | ~180 | **MEDIUM** |
| unknown | 6 | ~150 | **MEDIUM** |
| registry | 5 | ~45 | **LOW** |
| risk_gate | 5 | ~45 | **LOW** |
| backup | 2 | ~50 | **HIGH** |
| restore | 2 | ~50 | **HIGH** |

**Domänen mit 0 Routen in D.1-Inventar:** `notifications`, `telemetry`, `development_server`, `development_control_center`, `packaging` (als eigene Pfad-Domäne), `rescue_usb` (Stick-Pfade unter `rescue` / `rescue_build` klassifiziert).

**Größte Domain:** `rescue` (84 Routen, ~35 % aller Endpunkte)

**Aktive Domänen gesamt:** 12 von 19 definierten Kategorien

## Risiko-Legende

| Stufe | Bedeutung |
|-------|-----------|
| **LOW** | Read-only / Facade-only, keine Runner-Ausführung in Handler |
| **LOW–MEDIUM** | Plan-only / evidence_write, teils decoupled |
| **MEDIUM** | Governance, Diagnostics, Identifier-Pläne |
| **MEDIUM–HIGH** | Versioning mit `apply`-Routen |
| **HIGH** | Rescue, Backup, Restore, Build-Pfade |
| **CRITICAL** | Core Deploy execute/write (`/execute`, `/write/execute`, `real-write`) |

## Verteilung HTTP-Methoden

| Methode | Anzahl |
|---------|--------|
| POST | 226 |
| GET | 11 |
| PUT/DELETE/PATCH | 0 |

## Unknown-Routen (6) — Nachklassifizierung für D.2

| Route | Empfohlene Domain |
|-------|-------------------|
| `/setuphelfer-safe-rewrite-plan` | versioning |
| `/setuphelfer-controlled-rewrite-apply` | versioning |
| `/setuphelfer-branding-guard-check` | governance |
| `/legacy-runtime-coexistence-analysis` | versioning |
| `/legacy-runtime-safe-migration-recommendations` | versioning |
| `/legacy-upgrade-path-matrix` | versioning |
