# Preflight Backup Overview

## Warum vor Restore/Deploy sichern?

Spätere Eingriffe können fehlschlagen oder unbeabsichtigte Auswirkungen haben. Ein aktuelles Preflight-Backup minimiert das Risiko irreversibler Datenverluste.

## Wann blockiert Preflight?

Preflight respektiert Write-Safety-Hard-Stops:
- System-/Live-Medien
- unklare Geräte
- Windows-/Dualboot-Risikoziele

## Warum Confirmation-Token?

`preview` erzeugt plangebundenes Token. `execute` akzeptiert nur dieses Token für genau diesen Plan. Es gibt keine globale Freigabe.

## Warum kein Override in dieser Phase?

Diese Phase ist sicherheitsorientiert und defensiv. Override-Workflows mit erhöhtem Risiko sind bewusst nicht Teil der aktuellen Stufe.
