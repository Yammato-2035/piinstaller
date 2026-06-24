# GitHub Pytest 21:15 Investigation

Untersuchung: 2026-06-24 (lokal) · Zeiten unten in UTC und CEST (UTC+2).

## Run-Abgleich

| Run-ID | Zeit (UTC / CEST) | Workflow | Commit | Status | Conclusion | Gehört zu aktuellem origin/main? |
|--------|-------------------|----------|--------|--------|------------|----------------------------------|
| 28123262741 | 19:12:35 / **21:12** | CI | `64d1dbb` | completed | **failure** | nein (Vorgänger) |
| 28123437290 | 19:15:41 / **21:15** | CI | `dc1b159` | completed | **success** | nein (Vorgänger von HEAD) |
| 28123603561 | 19:18:47 / **21:18** | CI | `7e7721d` | completed | **success** | **ja (aktueller origin/main)** |
| 28123437281 | 19:15:41 / **21:15** | Security | `dc1b159` | completed | success | nein |
| 28123603642 | 19:18:47 / **21:18** | Security | `7e7721d` | completed | success | **ja** |

**Lokaler Abgleich (Phase 0):**

- `HEAD` = `origin/main` = `7e7721df920ff819a9be57b9e8a9c53260605973` (`7e7721d`)
- Keine unpushed Commits
- Preflight-Bundle: **nicht staged** (`git diff --cached` leer)

## Maßgeblicher Run

| Feld | Wert |
|------|------|
| **run_id** | `28123603561` |
| **commit** | `7e7721d` — `docs(evidence): finalize CI green loop audit 2026-06-24` |
| **workflow** | CI |
| **conclusion** | **success** |
| **url** | https://github.com/Yammato-2035/piinstaller/actions/runs/28123603561 |
| **pytest** | `3355 passed, 7 skipped` (Job-Log) |

Security maßgeblich: `28123603642` — success.

## Befund

**`old_run`** — Der sichtbare Pytest-Fehler um ca. **21:15 CEST** stammt vom CI-Lauf **`28123262741`** (Commit `64d1dbb`), der pytest um **21:15:12 CEST** mit 1 Failure beendet hat. Der **nächste** Push (`dc1b159`, Run **`28123437290`**, Start 21:15:41 CEST) war bereits **grün** (`3355 passed`). Aktueller `origin/main` (`7e7721d`) ist ebenfalls grün.

Kein aktueller Fehler auf `origin/main`. **Kein Fix erforderlich.**

## Fehlerklasse (historischer Run 28123262741)

| Feld | Wert |
|------|------|
| **Klasse** | `assertion_error` / `environment_error` |
| **Test** | `tests/test_rescue_telemetry_lan_proxy_v1.py::…::test_detect_lan_ip_skips_loopback` |
| **Meldung** | `AssertionError: '10.1.0.35' != '192.168.178.140'` |
| **Ursache** | GitHub-Runner-Netz (10.x) vs. hardcodierter Mock-Pfad; Socket-Probe vor subprocess-Mock |
| **Fix** | Bereits in `dc1b159` — Mock von `socket.socket` |

## Fix

**Nicht durchgeführt** (Investigation-only). Fehler war auf `64d1dbb` und ist ab `dc1b159` behoben.

## Nachweis

| Check | Status | Beleg |
|-------|--------|-------|
| origin/main HEAD | `7e7721d` | `git rev-parse origin/main` |
| CI auf HEAD | **success** | Run `28123603561` |
| Security auf HEAD | **success** | Run `28123603642` |
| Pytest auf HEAD | **3355 passed** | CI-Log Run `28123603561` |
| Fehler-Run 21:15 CEST | alter Commit | Run `28123262741` / `64d1dbb` |
| Nachfolgender grüner Run | success | Run `28123437290` / `dc1b159` |

## Gesamtstatus

**GRÜN** — Aktueller `origin/main` ist CI- und Security-grün. Der 21:15-Fehler ist ein **abgeschlossener, behobener Zwischenlauf**, nicht der maßgebliche Stand.
