# QEMU 212528 Ingest — Result

**Datum:** 2026-06-03  
**HEAD:** `e7f0bc2`  
**Gesamtstatus:** `blocked`

## Kurzfassung

1. **DCC:** Unter `release` erwartbar deaktiviert — **kein Portfehler**.
2. **QEMU 212528:** Nur ausgewertet, **kein** neuer Lauf.
3. **Fix 886a098:** Deploy + ISO-Rebuild vor Smoke; ModuleNotFound/Invalid Host **weg**.
4. **Neuer Blocker:** `agent_send_failed` → kein Guest-Report am Host.

## DCC

| Feld | Wert |
|------|------|
| Klassifikation | `dcc_not_available_expected_release_profile` |
| Portfehler ausgeschlossen | **yes** |

## QEMU

| Feld | Wert |
|------|------|
| `run_id` | `qemu_rescue_developer_autopilot_20260603_212528` |
| `autopilot_status` | `failed` |
| `guest_found` / `report_new` | false / false |
| serial | 133 260 B |
| Primär | `guest_report_payload_or_ingest_failure` |

## Nächster Schritt

Siehe `QEMU_212528_NEXT_PROMPT.md` — Agent-POST debuggen, Validator-Regex nachziehen. **USB gesperrt.**
