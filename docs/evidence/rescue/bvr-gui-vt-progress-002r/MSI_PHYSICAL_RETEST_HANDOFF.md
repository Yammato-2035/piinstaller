# MSI Physical Retest Handoff – PI-RS-BVR-GUI-VT-PROGRESS-002R

## Aktueller physischer Stand

| Feld | Wert |
|------|------|
| Letzter erfolgreicher BVR-Lauf | `e2e-rescue-msi-20260722-072255-05b6f187` |
| Payload | **1.10.1.2** |
| BVR | **passed** |
| GUI sichtbar | **nein** (Operator) |
| Gesamt | **`passed_with_gui_fallback`** |
| Run-Control | verbraucht durch diesen Lauf |

## Stick

- Gerät: Ultra Line /dev/sda (SN 24111412110686)
- SHA256: `5a7b0e8c23de04b7b5910494c51cd14b0e461d6fe61153f87796e1cc9422fad3`
- Build-Commit: `61bac2b3`

## Evidence

`docs/evidence/rescue/bvr-gui-vt-progress-002r/physical_runs/e2e-rescue-msi-20260722-072255-05b6f187/`

## GUI-Befund (dieser Boot)

1. HTTP ready + `auto-e2e-progress.html`
2. VT 7 vorbereitet (`fuser=skip`), `OPENVT_START` geloggt
3. Kein Xorg-Log, Chromium laut Runtime nicht sichtbar gestartet
4. Operator: keine grafische Oberfläche

## Nächster GUI-Retry (falls gewünscht)

1. Run-Control erneut schärfen (`enabled=true`, `consumed=false`, expected **1.10.1.2**)
2. SABRENT anschließen, MSI booten
3. Sichtbarkeitsnachweis (Foto) + neuen Import unter neuer Run-ID

## Status jetzt

`passed_with_gui_fallback` — physischer BVR-Nachweis vorhanden, GUI-Ziel nicht erreicht.
