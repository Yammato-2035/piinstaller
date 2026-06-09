# Rescue React Shell Architecture

**Version:** 1.7.10.0 · **RS-001:** yellow

## Zielstruktur

```text
GRUB → Live-System → Medium-Check → Rescue Shell → React UI (offline) → optionale Aktionen
```

## Frontend

```text
frontend/src/rescue/
├── RescueApp.tsx
├── RescueBootStatus.tsx
├── RescueMainMenu.tsx
├── RescueNetworkPanel.tsx
├── RescueEvidencePanel.tsx
├── RescueCompanionPanel.tsx
├── RescueAdvancedOptions.tsx
├── rescueApi.ts
├── rescueTypes.ts
└── i18n/{de,en}.json
```

Build: `scripts/rescue-live/build-rescue-react-ui.sh` → `build/rescue/ui/`

## Startoptionen

| Option | Phase |
|--------|-------|
| A: Browser/Kiosk `http://127.0.0.1:<port>` | bevorzugt |
| B: statische `file://` UI | Fallback ohne API |
| C: Tauri/WebView | später |
| D: Text-Fallback (`setuphelfer-rescue-start-assistant`) | nur bei UI-Fehler |

## Backend (statisch)

- `backend/rescue/rescue_boot_status.py`
- `backend/rescue/rescue_state.py`
- `backend/rescue/rescue_evidence_spool.py`
- `backend/rescue/rescue_machine_profile.py`

## Systemd (Konzept)

- `setuphelfer-rescue-ui.service` — kein `network-online.target`
- `setuphelfer-rescue-state.service` — oneshot
- `setuphelfer-rescue-evidence-spool.service` — best effort

## Nächster Schritt

SquashFS rebuild + FAT32-ESP payload update + Hardware-Retest.
