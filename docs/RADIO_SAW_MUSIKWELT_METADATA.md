# radio SAW / Musikwelt – Titel & Interpret (Metadaten)

## Website https://www.radiosaw.de/musikwelt

Die **Musikwelt**-Seite ist die Übersicht aller angebotenen Sender von radio SAW:

- **Hauptprogramm:** radio SAW (Simulcast in vier Regionen: Anhalt/Wittenberg, Halle/Leipzig, Harz/Niedersachsen, Magdeburg/Altmark)
- **Musikkanäle:** ROCKLAND, 1A Deutsche Hits, 70er, 80er, 90er, 2000er, 2010er, Neuheiten, Party, In the Mix (90er/80er/90er), Fitness, Relax, Urban Music, Rock Classic, Rock Alternative, Rock Balladen, Oldies, Synthie-Pop, Schlagerparty, Hits für Kids, Weihnachten

Die Seite listet Sender mit Bildern (von `backend.radiosaw.de`) und verlinkt auf den [Radioplayer](https://www.radiosaw.de/radioplayer). Eine **öffentliche JSON- oder REST-API** für „Now Playing“ (aktueller Titel/Interpret) ist im sichtbaren HTML/Seiteninhalt **nicht** dokumentiert oder verlinkt. Titel und Interpret auf der Website werden typischerweise per JavaScript aus dem laufenden Stream oder einer internen API geladen.

---

## Wie man Titel und Interpret bekommt

**Titel und Interpret** kommen bei radio SAW (und den Musikwelt-Streams) aus dem **Audio-Stream selbst** – über das **ICY-Metadaten-Protokoll** (Standard bei Shoutcast/Icecast-ähnlichen Streams).

### Ablauf

1. **HTTP-Anfrage an die Stream-URL** mit Header `Icy-MetaData: 1`.
2. **Antwort-Header auswerten:** `icy-metaint` gibt an, nach wie vielen Bytes Audio ein Metadaten-Block folgt.
3. **Stream lesen:** Nach jeweils `icy-metaint` Bytes kommt ein Metadaten-Block (erst 1 Byte Länge × 16, dann die Metadaten).
4. **Metadaten parsen:** Der Inhalt ist z. B. `StreamTitle='Interpret - Titel';` (optional `StreamUrl='...'`). Kodierung oft UTF-8 oder Latin-1.

Damit erhält man **Interpret** und **Titel** (getrennt nach dem Trennzeichen „ - “).

### Stream-URLs (Beispiele)

| Sender        | Stream-URL |
|---------------|------------|
| Radio SAW     | `https://stream.radiosaw.de/saw/mp3-128/` |
| SAW 70er      | `https://stream.radiosaw.de/saw-70er/mp3-192/` |
| SAW 80er      | `https://stream.radiosaw.de/saw-80er/mp3-192/` |
| SAW 90er      | `https://stream.radiosaw.de/saw-90er/mp3-192/` |
| SAW 2000er    | `https://stream.radiosaw.de/saw-2000er/mp3-192/` |
| Rockland      | `https://stream.radiosaw.de/rockland/mp3-192/` |
| SAW Party     | `https://stream.radiosaw.de/saw-party/mp3-192/` |
| SAW Schlagerparty | `https://stream.radiosaw.de/saw-schlagerparty/mp3-192/` |

Weitere Sender siehe [Musikwelt](https://www.radiosaw.de/musikwelt) bzw. `apps/dsi_radio/stations.py` und `frontend/src/components/RadioPlayer.tsx`.

### Manueller Test (ICY)

```bash
# Prüfen, ob der Stream ICY-Metadaten liefert
curl -sI -H "Icy-MetaData: 1" "https://stream.radiosaw.de/saw/mp3-128/"
# Erwartung bei ICY-Unterstützung: Header z. B. icy-metaint: 16000
```

---

## Einschränkung: Radio SAW / streamABC

Die URLs von radio SAW (z. B. `https://stream.radiosaw.de/saw/mp3-128/`) leiten per **302 Redirect** auf den Stream-Anbieter **streamABC** (vmg.streamabc.net) weiter. Dessen Server (streamABC/QuantumCast) liefert **keinen** Header `icy-metaint` – es werden also **keine ICY-Metadaten** ausgeliefert. Dadurch können Titel und Interpret für **alle Radio-SAW-Sender** (Hauptprogramm und Musikwelt-Kanäle) im PI-Installer **nicht** angezeigt werden.

- **Anzeige:** Es wird „Live“ bzw. der Sendername angezeigt; zusätzlich erscheint der Hinweis: *„Titel/Interpret für diesen Sender derzeit nicht verfügbar.“*
- **Technisch:** Das Backend setzt bei diesen Streams `metadata_unsupported: true` in der API-Antwort; Frontend und DSI-Radio zeigen dann den Hinweis an.

---

## Umsetzung im PI-Installer

Das Backend versucht, Titel/Interpret über ICY zu holen:

- **Backend:** `backend/app.py` – Funktionen `_parse_icy_metadata_from_stream`, `_parse_stream_title_from_icy`, `_fetch_icecast_metadata`. Für Hosts `stream.radiosaw.de` und `streams.rsa-sachsen.de` wird zuerst ICY genutzt (kein Icecast-`status-json.xsl`). Da der finale Stream von streamABC keine ICY-Header liefert, bleibt das Ergebnis leer; dann wird `metadata_unsupported: true` gesetzt.
- **API:** `GET /api/radio/stream-metadata?url=<STREAM_URL>` – liefert u. a. `title`, `artist`, `song`, `bitrate`, bei SAW/streamABC zusätzlich `metadata_unsupported: true` (5-Sekunden-Cache).
- **DSI-Radio / Frontend:** Rufen diese API auf; bei `metadata_unsupported` wird der Hinweis „Titel/Interpret für diesen Sender derzeit nicht verfügbar“ angezeigt.

Details zum Debugging: **docs/RADIO_METADATA_DEBUGGING.md**.

---

## Kurzfassung

| Frage | Antwort |
|-------|---------|
| Wo steht die Senderliste? | [radiosaw.de/musikwelt](https://www.radiosaw.de/musikwelt) (Übersicht + Radioplayer). Im Projekt: `stations.py`, `RadioPlayer.tsx`. |
| Woher kommen Titel & Interpret? | Theoretisch aus dem **Stream** per **ICY-Metadaten**. Bei Radio SAW liefert der Redirect-Zielserver (streamABC) **keine** ICY-Header → keine Anzeige möglich. |
| Warum bei SAW nichts? | Stream-URL leitet auf vmg.streamabc.net weiter; dort fehlt `icy-metaint`. |
| Was zeigt die App bei SAW? | „Live“ + Hinweis „Titel/Interpret für diesen Sender derzeit nicht verfügbar.“ |
