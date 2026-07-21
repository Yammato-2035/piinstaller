# MSI Physical Retest Handoff – PI-RS-BVR-GUI-VT-PROGRESS-002R

## Stick

- Gerät: Ultra Line /dev/sda (SN 24111412110686)
- Payload: **1.10.1.2**
- SHA256: `5a7b0e8c23de04b7b5910494c51cd14b0e461d6fe61153f87796e1cc9422fad3`
- Build-Commit: `61bac2b3`

## Erwarteter Boot

1. MSI GE63 vom Rettungsstick booten (GUI-Lab / `setuphelfer_mode=gui` + `setuphelfer_msi_e2e_auto=1`).
2. HTTP-Server :8765, `/health.json` ready.
3. Chromium: `http://127.0.0.1:8765/auto-e2e-progress.html`
4. GUI-VT: typisch 7 (fallback 8/9), TUI bleibt tty1.
5. Kanonische Datei: `/run/setuphelfer-rescue/canonical-bvr-progress.json`
6. Phasen: startup → … → backup → verify → restore → … → completed → shutdown
7. Nach Phase backup **kein** dauerhaftes Zurück auf sabrent_wait.
8. BVR unattended auf SABRENT; Auto-Shutdown.

## Sichtbarkeitsnachweis

Foto/Screenshot der GUI mit sichtbarer Phase, Zeitpunkt, Run-ID/Payload soweit angezeigt.

## Nach dem Lauf

Stick zurück, SETUP_LOGS importieren unter neuer Run-ID, Evidence unter:
`docs/evidence/rescue/bvr-gui-vt-progress-002r/physical_runs/<run-id>/`

## Status jetzt

`implemented_pending_physical_retest` — physischer MSI-Lauf steht aus.
