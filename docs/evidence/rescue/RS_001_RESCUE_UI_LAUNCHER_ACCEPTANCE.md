# RS-001 Rescue UI Launcher Acceptance

**Datum:** 2026-06-10

---

## Workspace Contract (1.7.11.0)

| Prüfung | Ergebnis |
|---------|----------|
| Launcher schreibt `rescue-ui-status.json` | **yes** |
| Fallback-TUI bei fehlendem Browser | **yes** |
| `review_required` / kein URL-only green | **yes** |
| Erwarteter Fallback-Status-Contract | **yes** |

Erwarteter Status bei fehlendem Browser:

```json
{
  "server_started": true,
  "browser_started": false,
  "display_mode": "fallback_tui",
  "menu_visible": true,
  "status": "review_required",
  "reason": "no_graphical_browser_available_or_not_started"
}
```

**Tool:** `scripts/rescue-live/test-rescue-ui-launcher-contract.sh`

---

## Stick SquashFS (1.7.10.1)

| Prüfung | Ergebnis |
|---------|----------|
| `react_launcher_contract_ok` | **false** (veraltete Skripte) |
| React/Kiosk | **blocked_missing_browser_or_display_runtime** |

Stick erfüllt Baseline 1.7.10.1 offline-first, aber **nicht** den erweiterten Acceptance-Contract aus 1.7.10.2+.
