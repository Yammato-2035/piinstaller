# Knowledgebase: Internetradio

Dokumentation externer Quellen und Referenzprojekte für die PI-Installer-Internetradio-Funktionen (DSI Radio, Backend-Suche, Logos, Metadaten).

---

## PI-Installer (piinstaller) – Projekt als Quelle

**Zweck**: Primäre Quelle für Senderlisten, Stream-URLs, Logos und Homepages der Sender im Projekt.

- **Repository**: piinstaller (PI-Installer-Projekt)
- **Senderliste / Stream-URLs**: `apps/dsi_radio/stations.py` (`RADIO_STATIONS`) – enthält `stream_url`, `logo_url`, `homepage` (Internetseite des Senders), `region`, `genre`.
- **Logos**: Neben Wikipedia/API werden Sender-Webseiten genutzt (z. B. **104.6 RTL**: Logo von https://www.104.6rtl.com/ – z. B. `favicon.ico` oder offizielles Logo von der Startseite).
- **Internetseiten der Sender**: Pro Sender wird `homepage` gespeichert (z. B. `https://www.104.6rtl.com/` für 104.6 RTL), Backend-API liefert `homepage` aus der Radio-Browser-API bzw. aus der lokalen Senderliste.
- **Stream-URLs / Ton / Metadaten**: `docs/INTERNETRADIO_STREAM_URLS.md` (Energy, radioeins, rbb 88.8), `apps/dsi_radio/gst_player.py` (User-Agent, Ton), `apps/dsi_radio/dsi_radio_qml.py` (Metadaten-Fallback), Backend `_fetch_icecast_metadata` / `_parse_icy_metadata_from_stream`.

**Wann heranziehen**: Sender-URLs prüfen, Homepage/Logo ergänzen, Abgleich mit Radio-Browser-API, Debugging Ton/Metadaten.

**Sender-Namen und Logos**:
- **Namen aus der API**: Die Radio-Browser-API liefert teils unschöne Namen (z. B. mit Unterstrichen, „_BIGCITYBEASTS.FM by rautemusic“). Im Backend und in der QML-Bridge werden Sendernamen normalisiert (führende Unterstriche entfernt, Suffix „ by rautemusic“ abgeschnitten). Den „echten“ Sendernamen liefert der Stream nur in ICY-Metadaten (z. B. `icy-name`) – der wird derzeit nicht für die Anzeige in der Senderliste genutzt.
- **Namen gezielter ermitteln**: Optional kann ein Suchbot (z. B. Websuche nach „Sender X Logo“ oder Radio-Browser-API-Suche nach URL/Name) genutzt werden, um zu einer Stream-URL den offiziellen Namen und ein Logo zu finden. Bisher: Namen/Logos aus `stations.py`, Radio-Browser-API und Wikipedia-Commons; bei Bedarf Erweiterung um automatische Namens-/Logo-Suche.
- **Logos nur als Logo**: MDR Aktuell, Deutschlandfunk und DLF Kultur nutzen ausschließlich reine Sender-Logos (kein Senderfoto): z. B. `Deutschlandfunk_Logo_2017.svg`, `Logo_mdr_AKTUELL_2016.png` von Wikimedia Commons. Radio Bob, SWR1 BW, HR1, rbb 88.8: Logos aus Wikipedia-Commons bzw. Sender-Webseite (rbb 88.8: Rbb_Logo_2017.08.svg).

---

## Radio Browser API

- **URL**: https://api.radio-browser.info/
- **Docs**: Server-spezifisch, z. B. https://de1.api.radio-browser.info/ oder https://de2.api.radio-browser.info/
- **Verwendung im Projekt**: Backend `backend/app.py` nutzt die API für `/api/radio/stations/search` (Land, Tag/Musikrichtung), Logo-Suche für deutsche Sender (`_radio_browser_favicon_by_name`), und die DSI-Radio-QML-Bridge lädt Senderlisten über das Backend.

**Wichtige Punkte** (laut API-Doku):

- Immer Serverliste per DNS-Lookup von `all.api.radio-browser.info` nutzen oder einen festen Server (z. B. `de1.api.radio-browser.info`) verwenden; direkte Links auf einen einzelnen Server können sich ändern.
- Sprechenden User-Agent senden (z. B. `PI-Installer/1.0`).
- `countrycode` (ISO 3166-1 alpha-2) statt veraltetes `country`-Feld; `stationuuid` statt `id` für übergreifende Referenzen.

---

## Referenz: radiobrowser-web-angular

**Zweck**: Weitere Quelle zur Klärung von Implementierungsdetails und typischen Problemen bei Internetradio (Stream-URLs, Codecs, Metadaten, API-Nutzung).

- **GitHub** (archiviert): https://github.com/segler-alex/radiobrowser-web-angular  
- **GitLab** (aktiv): https://gitlab.com/radiobrowser/radiobrowser-web-angular  

Angular-Webfrontend für die Radio Browser API. Zeigt, wie eine etablierte Anwendung:

- die Radio-Browser-API anbindet (Suche, Senderdetails, Favicons),
- Stream-URLs handhabt (inkl. Redirects und `url_resolved`),
- mit verschiedenen Codecs (MP3, AAC) und Metadaten umgeht.

**Wann heranziehen**:

- Unklare oder wechselnde Stream-URLs (z. B. addradio, streamonkey, Icecast).
- Unterschiedliches Verhalten pro Sender (z. B. Ton bei 1Live, kein Ton bei radioeins/Energy): Referenz, wie andere Clients User-Agent, Redirects und Quellen konfigurieren.
- API-Felder (codec, lastcheckok, favicon, tags, countrycode) und Suchparameter.
- Favicon-/Logo-URLs und Fallbacks.

**Hinweis**: Das Projekt ist auf GitLab unter der Radio-Browser-Organisation weitergeführt; bei Fehlern oder Erweiterungen der API lohnt ein Blick in Issues und Merge Requests dort.

---

## Referenz: Shortwave (GNOME)

**Zweck**: GNOME-Internetradio-App mit großer Senderdatenbank; Referenz für Aufnahme-Logik, Track-Erkennung und Metadaten-Nutzung.

- **GitLab**: https://gitlab.gnome.org/World/Shortwave  
- **GNOME Apps**: https://apps.gnome.org/Shortwave/  

Kurzüberblick zu Aufnahme und Qualität (Moderation/Werbung) siehe **`docs/SHORTWAVE_RECORDING.md`**.

**Wann heranziehen**:

- Aufnahme-Funktion (Track-Erkennung, Min/Max-Trackdauer, Speicherordner).
- Metadaten-basierte Track-Trennung und Umgang mit Werbung/Moderation.
- Integration mit Radio-Browser-API bzw. großer Senderdatenbank (50.000+ Sender).
- UI/UX für Sendersuche, Favoriten, Wiedergabe.

**Hinweis**: Lizenz GPL-3.0; Entwicklung auf GitLab, Kommunikation u. a. auf Matrix (#shortwave:gnome.org).

---

## Weitere relevante Links

- **Radio Browser API (Rust)**: https://gitlab.com/radiobrowser/radiobrowser-api-rust (aktuelle Server-Implementierung, Release Notes, Migration von der alten API).
- **API-Webservice (Legacy-Doku)**: http://www.radio-browser.info/webservice (ältere API; Migration auf neue Server empfohlen).
- **PI-Installer-interne Doku**: `docs/RADIO_METADATA_DEBUGGING.md` für Metadaten-Debugging, Backend-Checks und Wayfire/X11; `docs/SHORTWAVE_RECORDING.md` für Shortwave-Aufnahme-Logik und Qualität bei Moderation/Werbung.

---

## Kurz: Wann welche Quelle

| Thema | Quelle |
|-------|--------|
| Senderliste, Stream-URLs, Homepages, Logos (104.6 RTL etc.) | **PI-Installer (piinstaller)**: `apps/dsi_radio/stations.py`, `INTERNETRADIO_STREAM_URLS.md` |
| Sendersuche, Logos, API-Parameter | Radio Browser API (Docs), Backend `app.py` |
| Implementierungsmuster, Stream-/Client-Probleme | radiobrowser-web-angular (GitLab/GitHub) |
| Aufnahme, Track-Erkennung, Metadaten-Trennung | Shortwave (GitLab GNOME), `SHORTWAVE_RECORDING.md` |
| Metadaten, Debug-Logs, Backend | `RADIO_METADATA_DEBUGGING.md` |
| GStreamer, Ton, User-Agent | `apps/dsi_radio/gst_player.py`, PyQt-Referenz in `dsi_radio.py` |
