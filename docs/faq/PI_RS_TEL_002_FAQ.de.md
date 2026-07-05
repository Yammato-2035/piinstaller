# PI-RS-TEL-002 FAQ (DE)

## Was ist neu gegenüber PI-RS-TEL-001?

Reachability-Prüfung, profilabhängiges Runtime-Gate und Offline-Queue-**Vorschau** — ohne Auto-Replay.

## Sendet die Reachability-Prüfung Telemetrie?

**Nein.** Nur HTTP-Probe zum Lab-Server, keine Payload.

## Wann wird live gesendet?

Nur bei explizitem `allow_send_when_reachable=true` **und** `SETUPHELPER_ENABLE_LIVE_LAB_TELEMETRY_TEST=1` **und** erreichbarem Endpoint.

## Gibt es eine echte Offline-Queue?

**Nein.** Nur redigierte Preview-Dateien unter `docs/evidence/runtime-results/rescue-lab-telemetry/offline-queue-preview/`.

## Release-Profil?

Lab-Routen liefern HTTP 403 `feature_disabled`. DCC 404 im Release ist erwartbar.

## Nächste Phase?

**PI-RS-TEL-003** — manuelle Live-Lab-Validierung nach Profil-Deploy.
