# PI-RS-TEL-001 FAQ (DE)

## Was macht PI-RS-TEL-001?

Erster **Lab-only** Sendefluss für synthetische Rescue-Stick-Telemetrie vom piinstaller-Workspace zum privaten Telemetrieserver (TEL-012).

## Sendet das echte Hostdaten?

**Nein.** Nur synthetische Preview-Payloads ohne MAC, IP, Hostname, Seriennummern, Rohlogs oder Secrets.

## Wann wird gesendet?

Nur bei explizitem `POST /api/rescue/telemetry/lab/send-preview` im Lab-/Dev-Profil. Kein automatisches Senden beim Start.

## Was passiert ohne Secret?

`blocked_missing_secret` — kein Netzwerk-Send, klare Operator-Meldung.

## Ist das produktionsreif?

**Nein.** `production_ready=false` überall. HMAC-Erfolg = Lab-Akzeptanz, keine Produktivfreigabe.

## Nächste Phase?

**PI-RS-TEL-002** — Netzwerk-Gate + Offline-Queue-Vorschau (noch ohne echten Replay).
