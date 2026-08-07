# ASUS-00 — Failed to start setuphelfer-rescue-ui.service

Stand: 2026-08-07

## Beobachtung

Nach Fix von `setuphelfer_start_assistant=1` bootet ASUS-00 weiter, meldet dann
`Failed to start setuphelfer-rescue-ui.service` und „steht“.

## Ursache

`setuphelfer-rescue-ui.service` war in `multi-user.target.wants` **ohne**
`ConditionKernelCommandLine=setuphelfer_kiosk=1` und belegt `TTYPath=/dev/tty1`
mit `Restart=on-failure`.

Auf ASUS-00 (`setuphelfer_kiosk=0`, `setuphelfer_mode=text`) beendet
`setuphelfer-rescue-gui-start` mit Exit **5** (text skip). Das gilt als Failure →
Restart alle 5 s → tty1-Storm / Konflikt mit `setuphelfer-rescue-start-assistant`
→ System wirkt hängend.

## Fix (Workspace + SquashFS)

1. Unit: `ConditionKernelCommandLine=setuphelfer_kiosk=1`
2. Unit: `SuccessExitStatus=5` (Gürtel/Hosenträger)
3. SquashFS neu gepackt:
   SHA256 `d704ed4ef9dfa5fb5c090305604964b4c16b2b7b99771d3bb1b997bad02f1d68`

## Stick

Payload-Update auf FAT32-ESP nötig (kein Full-Rewrite). Offizielles Skript mit
Operator-Bestätigungen — siehe Chat.

## Sofort-Workaround auf dem hängenden Notebook (ohne Stick-Update)

Falls Eingabe auf anderer VT möglich:
`systemctl stop setuphelfer-rescue-ui.service`
dann `systemctl start setuphelfer-rescue-start-assistant.service`
