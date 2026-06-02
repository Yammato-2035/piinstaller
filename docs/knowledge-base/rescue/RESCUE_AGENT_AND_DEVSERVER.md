# Rescue Agent und Development Server (KB)

## Was ist fertig

- Fleet-Heartbeat-Payload-Fix mit `agent_state`
- Discovery-/Pairing-/E2EE-/NFTables-/System-Report-Stub im Backend
- API-Stub-Routen `/api/rescue-agent/*`
- Dashboard-Stub für Rescue-Agent-Sessions
- Live-Menü-Frontend-Stub

## Was ist Stub/Contract

- E2EE als Envelope-Stub
- Discovery als kontrollierter Stub (ohne Internet/Cloud)
- NFTables nur Preview/Validator (`apply_allowed=false`)

## Was explizit nicht produktiv ist

- Kein ISO-Build, kein QEMU, kein USB-Write
- Keine echten Hardware-Schreibaktionen
- Keine dauerhaften Pairing-Secrets im Image

## Datenschutz

- Keine Klartext-Seriennummern
- Keine persistierten Klartext-IP-Daten
- Standort nur als freiwilliger Operator-Hinweis
