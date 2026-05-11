# Security Review: DSI/Radio (DSI-Radio, Freenove)

## Kurzbeschreibung

Radio-Streaming, DSI-Theme, Favoriten, Display-/Icon-Konfiguration. Endpunkte: /api/radio/stream-metadata, logo, stream, stations/search, dsi-theme, dsi-config/favorites, display, icons. Lesen/Schreiben von Konfiguration und Stream-URLs.

## Angriffsfläche

- API: URLs (Streams), Favoriten-Listen, Theme/Display-Parameter, Dateipfade (Icons).
- Eingaben: Freie Textfelder (URLs), Pfade für Icons.

## Schwachstellen

1. **URL-Validierung:** Stream-URLs müssen validiert werden (Schema, Host); keine file:// oder internal URLs, die zu SSRF führen könnten.
2. **Pfad-Traversal:** Icons/Display-Pfade dürfen nicht aus dem erlaubten Verzeichnis herausführen.
3. **Storage:** Konfiguration wird in Dateien geschrieben; keine unsicheren Pfade aus Request übernehmen.

## Empfohlene Maßnahmen

- URL-Whitelist: nur http(s), erlaubte Ports; keine file:, localhost (außer explizit erlaubt).
- Pfad-Validierung: realpath, Unterpfad von konfiguriertem DSI-Config-Verzeichnis.
- Keine Roh-Request-Pfade in write-Operationen.

## Ampelstatus

**GELB.** Relevante Schwächen (URL, Pfad); kein ROT wenn keine direkte Ausführung von URLs.

## Betroffene Dateien

- backend/app.py: /api/radio/* (ca. 1356+).
- frontend: DsiRadioSettings, RadioPlayer, DSI-View.
