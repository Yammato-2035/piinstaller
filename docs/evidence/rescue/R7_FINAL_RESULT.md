# R.7 — Final Result

**Kampagne:** `CAMPAIGN_R7_HARDWARE_BOOT_PERSISTENCE_VALIDATION`  
**Datum:** 2026-06-10

## Zusammenfassung

R.7-Ziel (Hardware-Nachweis des R.6 Boot-Persistence-Hooks) ist **nicht erfüllt**. Der Stick enthält ein **pre-R.6**-Squashfs ohne `boot-evidence-init`. Kein MSI-Boot in dieser Kampagne dokumentiert. `boot_marker` fehlt.

## HEAD / Version

| Feld | Vorher | Nachher |
|------|--------|---------|
| HEAD | `57e30d9` | `57e30d9` (kein Commit) |
| `project_version` | 1.7.17.0 | 1.7.17.0 |
| Runtime API | 1.7.13.2 | 1.7.13.2 (unverändert) |

## ISO

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| SHA256 | `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143` |
| R.7 Rebuild | **nicht ausgeführt** (`LB_EXIT=30`, Operator-Gate) |

## USB

| Feld | Wert |
|------|------|
| R.7 Write | **nicht ausgeführt** (`OPERATOR_USB_WRITE_FREIGABE` unset) |
| Letzter Verify | **success** (`fat32_esp_write_20260613_171403`) |
| Stick-Label / GPT | `SETUPHELFER` / `SETUPHELFER_RESCUE` |

## SquashFS (Stick)

| Check | Ergebnis |
|-------|----------|
| chromium, openbox, xinit, rescue.html, telemetry | FOUND |
| boot-evidence-init, persistence v4, boot_marker | **MISSING** |
| Entscheidung | **blocked_runtime** |

## MSI / Operator

| Feld | Wert |
|------|------|
| Hardware-Boot beobachtet | **nein** |
| Evidence-Doc | `R7_OPERATOR_BOOT_OBSERVATION.md` (leer) |

## Boot Marker

| Feld | Wert |
|------|------|
| `boot_marker.md` | **MISSING** |
| `boot_marker.json` | **MISSING** |
| Bewertung | **R7_BOOT_MARKER_MISSING** |

## RS-001

**red** — kein echter Hardware-Nachweis, keine Runtime-Evidence auf Stick.

## R.6 Workspace-Status

R.6-Code **vollständig im Workspace**, Unit-Tests **5/5 OK**, aber **nicht committed** und **nicht im Stick-Image**.

## Phasen-Übersicht

| Phase | Ergebnis |
|-------|----------|
| 0 Gate | dokumentiert, Runtime-Drift notiert |
| 1 R.6 Validation | workspace OK, deployment pending |
| 2 ISO Build | blocked (Operator sudo) |
| 3 SquashFS | blocked_runtime |
| 4 USB Write | blocked (Freigabe + blocked_runtime) |
| 5 MSI Boot | nicht dokumentiert |
| 6 Runtime Evidence | `/setuphelfer-evidence/` fehlt |
| 7 Boot Marker | R7_BOOT_MARKER_MISSING |
| 8 RS-001 | red |
| 9 Abschluss | dieser Bericht |

## Nächster sinnvoller Schritt (Operator)

1. **R.6 committen** (separater Freigabe-Schritt)
2. **Prepare + Controlled ISO Build** im Operator-TTY:
   ```bash
   sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
     --operator-confirm-build --profile standard
   ```
3. **SquashFS erneut prüfen** — `boot-evidence-init` FOUND, persistence v4
4. **USB Write** mit `OPERATOR_USB_WRITE_FREIGABE=1`
5. **MSI-Boot** + `R7_OPERATOR_BOOT_OBSERVATION.md` ausfüllen
6. **Stick zurück** → prüfen `setuphelfer-evidence/boot/boot_marker.md`

Erst dann R.7 erneut mit Erfolgskriterium bewerten.

## Verbotene Aktionen (eingehalten)

Kein Deploy, kein USB-Write, kein Commit, kein apt, kein Backup/Restore.
