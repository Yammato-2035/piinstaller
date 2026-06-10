# RS-001 React Rescue Hardware Retest — Level 6 Ergebnis

**Datum:** 2026-06-10  
**HEAD:** `01ffba3`  
**Version:** `1.7.11.0`  
**SquashFS SHA256:** `a3e58964ffffe032fd7e543e5e28bd64156981347647a0ba9208101cb9d7726d`  
**RS-001 Status:** **yellow**  
**Lauf-Status:** **Phase 0 bestanden — Operator-Hardware-Retest Level 6 ausstehend**

---

## Phase 0 — Stick Acceptance (bestanden)

| Prüfung | Wert |
|---------|------|
| `acceptance_status` | **ok** |
| `exit_code` | **0** |
| `hardware_retest_allowed` | **true** |
| Level 1 FAT32/Hash | **ok** |
| Level 2 SquashFS Content | **ok** (1.7.11.0) |
| Level 3 Launcher/Fallback | **ok** |
| Level 4 GRUB Branding | **ok** |
| Network Menu Contract | **ok** |

---

## Phase 1 — Operator Hardware Boot (ausstehend)

Der Agent kann keinen physischen UEFI-Boot auf MSI/Referenzhardware ausführen.  
**Kein Level-6-Befund mit Payload `1.7.11.0` vorliegend.**

Host-Readback ESP (vor Retest): keine `setuphelfer/logs/`, keine `setuphelfer/evidence/boot/` — nur Writer-Metadaten.

---

## Hardware-Befund Level 6 (1.7.11.0)

| Feld | Wert |
|------|------|
| Hardware | MSI / Referenzhardware — **pending** |
| UEFI USB visible | **pending** |
| GRUB visible | **pending** |
| GRUB branding/theme visible | **pending** (Acceptance L4 ok auf Host) |
| Kernel | **pending** |
| Live system | **pending** |
| React/Kiosk visible | **pending** |
| Fallback-TUI visible | **pending** |
| Only URL printed | **pending** |
| Status action | **pending** |
| Log export action | **pending** |
| Network action crashes | **pending** |
| Network returns to menu | **pending** |
| Live-Medium warning | **pending** |
| Failed units before menu | **pending** |
| Evidence on USB | **no** (vor Retest) |

---

## Referenz: vorheriger Retest (1.7.10.1, `0b303d3…`)

| Feld | Wert |
|------|------|
| Fallback-TUI | ja, Status/Logs OK |
| GRUB branding | **nein** |
| Netzwerk | **crash** |
| React/Kiosk | **nein** (Browser fehlt im SquashFS) |

Erwartung für 1.7.11.0: GRUB-Theme sichtbar, Netzwerk crash-safe, Fallback-TUI weiterhin akzeptabel für RS-001 green.

---

## Klassifikation

```text
RS-001: yellow
Reason: stick acceptance ok; hardware level 6 retest not yet executed on 1.7.11.0
Next: operator phase-1 boot on MSI; then re-run USB log export and update this document
```

**Kein Fake-Green** — RS-001 wird erst green, wenn echter Hardware-Befund alle Green-Kriterien erfüllt.

---

## Operator-Checkliste (Phase 1)

1. Rechner herunterfahren, Stick einstecken, UEFI → USB
2. GRUB mit Setuphelfer-Theme fotografieren
3. „Setuphelfer Rettung starten“
4. Menü prüfen (Fallback-TUI oder React/Kiosk)
5. Status anzeigen, Logs auf Stick schreiben, Netzwerk testen
6. Kein Backup/Restore/Repair/Install

Evidence-Pfad nach Boot: `docs/evidence/runtime-results/rescue/rs001_level6_hardware_retest_from_usb/`
