# FAQ: Rescue Developer Agent Profile (DE)

## Wird der Public Rettungsstick automatisch senden?

**Nein.** Public-Profil: `ENABLED=false`, `AUTO_UPLOAD=false`.

## Wo liegt das Developer-Profil?

`build/rescue/profiles/developer/`

## Wird in diesem Schritt ein ISO gebaut?

**Nein.** Nur Profil-Dateien und Validierung.

## Brauche ich einen Development Server?

Ja, für sinnvolle Telemetrie — local_lab sendet an `127.0.0.1:8000` oder private LAN-URL.
