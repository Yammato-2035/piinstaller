# PI-RS-MSI-GUI-003 — Root Cause Analysis

Stand: 2026-07-12  
Quelle: `docs/evidence/pi_rs_msi_retest_002/` Session `20260712_111206_boot`

## Zeitpunkt der TUI-Beschädigung

| Klassifikation | Befund |
|----------------|--------|
| **confirmed** | Operator meldet visuelle TUI-Zerstörung während/nach Boot-Progress |
| **strongly_supported** | `boot-timeline.jsonl` 11:12:22 enthält `x11_starting` mit GUI-Meldung |

Timeline vor `x11_starting`: `network_probe_started` (11:12:14).  
Danach: `backend_starting`, `rescue_boot_status_visible` (Abschluss).

## Komponente: `x11_starting`

| Klassifikation | Befund |
|----------------|--------|
| **confirmed** | `scripts/rescue-live/image/setuphelfer-rescue-boot-progress` — statisches `phase_map[6]=x11_starting` und Schritt „Grafische Oberfläche wird gestartet …“ |

Die GUI-Sperre in PI-RS-MSI-GUI-002 blockiert `openvt`/`startx`, beeinflusst aber **nicht** die Boot-Progress-Phasenplanung.

## Komponente: tty1-Schreibzugriff

| Klassifikation | Befund |
|----------------|--------|
| **strongly_supported** | Boot-Progress und Whiptail-TUI nutzen beide `/dev/tty1` |
| **confirmed** | `setuphelfer-rescue-boot-progress.service` läuft parallel vor `getty@tty1` und TUI-Entrypoint |

Unter MSI-Compat setzt `show_tty` zwar `force=0` und `tty1_clear_allowed=false` blockiert Clears — **die Timeline-Phase `x11_starting` wurde dennoch erzeugt** und protokolliert den GUI-Pfad.

| Klassifikation | Befund |
|----------------|--------|
| **strongly_supported** | `console-shield` Schema v1 kannte nur `tty1_clear_allowed`, kein `tty1_write_allowed` |

## Whiptail-Übernahme von tty1

| Klassifikation | Befund |
|----------------|--------|
| **confirmed** | `setuphelfer-rescue-tui.sh` startet Whiptail auf tty1 via `setuphelfer_rescue_whiptail_tty` |
| **strongly_supported** | Race: Boot-Progress-Loop (8 Schritte × 8s MSI-Intervall) überlappt mit TUI-Start |

## Warum `gui_available=false` den Boot-Progress nicht steuerte

| Klassifikation | Befund |
|----------------|--------|
| **confirmed** | `gui-availability.json` wird von GUI-Watchdog/common geschrieben, **nach** Boot-Progress-Phasenplanung |
| **confirmed** | Boot-Progress nutzte feste `steps[]`/`phase_map[]` ohne `resolve_rescue_boot_profile()` |

## Stale GUI-Logs

| Klassifikation | Befund |
|----------------|--------|
| **confirmed** | `gui-start.log` / `rescue-ui-status.json` aus Session `20260712_015909` in neuer Evidence |
| **confirmed** | `setuphelfer_rescue_gui_chain_log_init` erzeugte separate `_gui`-Session-ID, nicht Boot-Session |
| **confirmed** | `mirror_evidence_file` kopierte Dateien ohne Session-Frische-Prüfung |

## Versionsdrift

| Klassifikation | Befund |
|----------------|--------|
| **confirmed** | ESP-Metadaten `1.10.0.15`, SquashFS-intern `config/version.json` = `1.10.0.12` |
| **confirmed** | Repack schrieb `VERSION` + `rescue_payload_version.json`, aber **nicht** `config/version.json` |

## Zusammenfassung Root Cause

1. **confirmed** — Boot-Progress erzeugt `x11_starting` unabhängig von MSI-GUI-Sperre.  
2. **strongly_supported** — Paralleler tty1-Zugriff Boot-Progress ↔ Whiptail ohne Ownership-Modell.  
3. **confirmed** — Session-Evidence ohne Boot-Session-Bindung → stale GUI-Logs.  
4. **confirmed** — Repack synchronisierte `config/version.json` nicht.
