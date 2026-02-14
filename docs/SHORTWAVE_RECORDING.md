# Shortwave: Aufnahme von Liedern und Qualität bei Moderator/Werbung

Kurze Übersicht, wie die GNOME-App **Shortwave** Aufnahmen handhabt und was das für die Qualität bei Moderations- oder Werbeunterbrechungen bedeutet. Relevanz für eine mögliche Aufnahme-Funktion in der DSI-Radio-App.

## Wie Shortwave Aufnahmen handhabt

- **Drei Aufnahme-Modi:**
  - **Save All Tracks:** Alle erkannten Tracks werden automatisch gespeichert.
  - **Decide for Each Track:** Es wird temporär mitgeschnitten; pro Track kann entschieden werden, ob er gespeichert wird.
  - **Record Nothing:** Nur Wiedergabe, keine Aufnahme.

- **Einstellungen:**
  - Speicherordner für Aufnahmen konfigurierbar.
  - **Minimal- und Maximal-Dauer** pro Track (z. B. um sehr kurze Stücke oder lange Werbeblöcke auszufiltern).
  - Tracks können während der Wiedergabe zum Speichern markiert werden; die Aufnahme wird dann beim Ende des Stücks abgeschlossen und gespeichert.

- **Track-Erkennung:** Shortwave nutzt automatische Track-Erkennung (Metadaten vom Stream). Über 50.000 Sender werden unterstützt.

## Qualität bei Moderator und Werbung

- **Stream = eine durchgehende Quelle:** Was gesendet wird (Musik, Moderation, Werbung), kommt in derselben technischen Qualität (Bitrate, Codec). Es gibt keine getrennten „Kanäle“ für Musik und Werbung.

- **Aufnahme = Mitschritt des Streams:** Es wird der laufende Stream mitgeschnitten. Läuft gerade Werbung oder Moderation, ist genau das in der Aufnahme – in derselben Qualität wie der Rest. Die **technische Qualität** (z. B. 128 kbps MP3) bleibt gleich; der **Inhalt** (Lied vs. Werbung) ändert sich.

- **Wie Shortwave die „Qualität“ des Liedes sichert:**
  - Über **Metadaten/Track-Erkennung**: Sobald ein neuer Titel (Artist/Title) erkannt wird, kann ein neuer Track begonnen werden; beim nächsten Wechsel (z. B. Moderation/Werbung) endet der Track. So entstehen **saubere Schnitte** zwischen Liedern und Nicht-Musik.
  - Über **Mindest-/Höchstlänge**: Kurze Stücke (z. B. Jingles) oder sehr lange Blöcke (Werbung, Moderation) können per Min/Max-Dauer ausgeschlossen werden.
  - **„Decide for Each Track“**: Nutzer können nur die gewünschten Tracks markieren; der Rest wird verworfen. So wird inhaltlich nur Musik gespeichert, Werbung/Moderation wird nicht mitgespeichert.

- **Fazit:** Die **Audio-Qualität** (Bitrate) ist über den ganzen Stream hinweg gleich. Die **inhaltliche Qualität** (nur Lieder, ohne Werbung/Moderation) wird durch Track-Erkennung, Längenfilter und manuelle Auswahl gesichert, nicht durch eine andere technische Qualität von Musik vs. Werbung.

## Übertrag auf DSI-Radio / PI-Installer

Falls eine Aufnahme-Funktion für die DSI-Radio-App geplant ist, wären sinnvoll:

1. **Metadaten-basierte Trennung:** Wie Shortwave – bei Wechsel von Title/Artist einen neuen „Track“ beginnen und nur solche Blöcke als Lied speichern, die z. B. eine Mindestlänge haben.
2. **Min/Max-Trackdauer:** Konfigurierbare Grenzen (z. B. 2–10 Minuten), um Jingles und Werbeblöcke auszufiltern.
3. **Speicherordner und Format:** Konfigurierbarer Pfad, einheitliches Format (z. B. MP3/OGG) in Stream-Qualität.
4. **Optional:** Stille-Erkennung (Silence Detection), um Werbepausen zu überspringen – erhöht Komplexität, kann aber die Trennung von Lied und Werbung verbessern.

Die Qualität des gespeicherten Liedes entspricht dann der Stream-Qualität; die „Sauberkeit“ (nur Musik, ohne Moderator/Werbung) kommt von Track-Grenzen und Filterung, nicht von einer höheren technischen Qualität der Musik im Stream.
