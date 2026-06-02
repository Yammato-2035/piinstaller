# Controlled ISO Build — Squashfs Review

**Datum:** 2026-06-02  
**Pfad:** `build/rescue/live-build/setuphelfer-rescue-live/binary/live/filesystem.squashfs`

| Feld | Wert |
|------|------|
| Größe | 433651712 B |
| Typ | Squashfs 4.0, xz compressed |
| mtime | 2026-06-02 21:58:15 |

## Pflichtinhalte

| Prüfpunkt | Ergebnis |
|-----------|----------|
| filesystem.squashfs vorhanden | **yes** |
| `/opt/setuphelfer-rescue` | **yes** (MANIFEST, backend, venv, frontend/dist) |
| `setuphelfer-dev-agent.service` | **yes** |
| `setuphelfer-backend.service` + enable wants | **yes** |
| `setuphelfer.service` + enable wants | **yes** |
| `devserver_agent/` (CLI für Guest-Smoke) | **yes** |
| `rescue_agent/` Backend-Modul | **no** (nicht im Temp-Bundle; Contract-Stubs nur im Workspace) |
| Produktive E2EE-Behauptung | **no** — Bundle-Runtime, kein Live-E2EE-Nachweis |

Dev-Agent-Unit enthält `Environment=PYTHONPATH=/opt/setuphelfer-rescue` und `backend.devserver_agent.cli --qemu-host-fallback`.

## Bewertung

**Status: ok**

Squashfs-Validator Exit **0**. Fehlendes `rescue_agent/`-Modul im Bundle ist dokumentiert, blockiert Guest-Agent-Smoke über `devserver_agent` nicht.
