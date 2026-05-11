# Radio-Metadaten Debugging Strategie

## Problem
RDS/Streamdaten werden nicht angezeigt: Kein Sendungsname, keine Audioqualität, kein Titel, kein Interpret.

## Diagnose-Schritte

### 1. Backend-Verbindung prüfen
Das Backend muss laufen, damit Metadaten abgerufen werden können.

```bash
# Prüfen ob Backend läuft
curl http://127.0.0.1:8000/api/radio/stream-metadata?url=https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3

# Backend starten falls nicht aktiv
cd /home/gabrielglienke/Documents/PI-Installer/backend
python3 -m uvicorn app:app --host 127.0.0.1 --port 8000
```

### 2. Debug-Dateien prüfen
Die App schreibt Debug-Informationen in:
- `~/.config/pi-installer-dsi-radio/metadata_debug.json` - Geholte Metadaten
- `~/.config/pi-installer-dsi-radio/metadata_error.log` - Fehler beim Abruf
- `~/.config/pi-installer-dsi-radio/metadata_applied.json` - Angewendete Metadaten
- `~/.config/pi-installer-dsi-radio/backend_check.log` - Backend-Verbindungsprobleme

```bash
# Debug-Dateien anzeigen
cat ~/.config/pi-installer-dsi-radio/metadata_debug.json
cat ~/.config/pi-installer-dsi-radio/metadata_error.log
cat ~/.config/pi-installer-dsi-radio/backend_check.log
```

### 3. Mögliche Ursachen

#### Backend nicht erreichbar
- **Symptom**: `backend_check.log` zeigt Verbindungsfehler
- **Lösung**: Backend starten (siehe Schritt 1)

#### Metadaten werden nicht vom Stream geholt
- **Symptom**: `metadata_debug.json` zeigt leere oder unvollständige Metadaten
- **Ursachen**:
  - Stream unterstützt keine ICY-Metadaten
  - Icecast status-json.xsl nicht verfügbar
  - Timeout beim Abruf
- **Lösung**: 
  - Prüfen ob Stream ICY-Metadaten unterstützt: `curl -H "Icy-MetaData: 1" <STREAM_URL>`
  - Manuell Metadaten-URL testen: `curl <BASE_URL>/status-json.xsl`

#### Metadaten werden nicht angezeigt
- **Symptom**: `metadata_applied.json` zeigt Metadaten, aber UI zeigt nichts
- **Ursachen**:
  - UI-Updates werden nicht ausgeführt
  - Labels sind leer oder versteckt
- **Lösung**: 
  - Prüfen ob `_apply_metadata()` aufgerufen wird
  - Prüfen ob Labels korrekt initialisiert sind

### 4. Wayfire vs X11

Falls Metadaten korrekt geholt werden, aber nicht angezeigt werden, könnte Wayfire das Problem sein.

#### Wayfire prüfen
```bash
# Aktueller Window Manager
echo $XDG_SESSION_TYPE
echo $WAYLAND_DISPLAY

# Wayfire-Regeln prüfen
cat ~/.config/wayfire.ini | grep -A 5 "pi-installer-dsi-radio"
```

#### Auf X11 umstellen
Falls Wayfire Probleme verursacht:

1. X11-Session starten:
```bash
# In ~/.xinitrc oder Display Manager
export XDG_SESSION_TYPE=x11
startx
```

2. Oder Wayfire-Regeln anpassen:
```bash
# Wayfire-Regel für DSI-Radio prüfen/anpassen
wayfire-config
```

### 5. Manuelle Tests

#### Metadaten direkt testen
```bash
# Backend-Endpoint direkt testen
curl "http://127.0.0.1:8000/api/radio/stream-metadata?url=https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3"
```

#### Stream-Player testen
```bash
# Stream direkt abspielen und Metadaten prüfen
mpv --no-video "https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3"
# Metadaten sollten in der Ausgabe erscheinen
```

## Implementierte Verbesserungen

1. **Debug-Logging**: Alle Metadaten-Abrufe werden geloggt
2. **Backend-Check**: Verbindungsprobleme werden erkannt und geloggt
3. **UI-Verbesserungen**:
   - Display nutzt jetzt volle Breite oben
   - Logo oben links eingeblendet
   - Größere Schriftarten (22px für Sender, 16px für Titel)
   - 3D-Effekt für den Rahmen (als ob das Display tiefer liegt)

## Nächste Schritte

1. App starten und Radio abspielen
2. Debug-Dateien prüfen
3. Falls Backend nicht erreichbar: Backend starten
4. Falls Metadaten leer: Stream-URL prüfen
5. Falls weiterhin Probleme: Wayfire-Regeln prüfen oder auf X11 umstellen
