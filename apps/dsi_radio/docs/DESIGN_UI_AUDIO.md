# DSI Radio – UI-Design & Audio-Features

## Frequenzanzeige = Spektrumanalysator?

**Ja, technisch eine vereinfachte Form.** Die Anzeige „Frequenzbandanzeige (klassisch)“ (`SpectrumBandWidget`) arbeitet wie ein **Band-Spektrumanalysator**:

- **Eingang:** Echtzeit-Audio vom Stream (GStreamer `level`-Element liefert keine Frequenzdaten; die Bänder kommen aus einem **FFT** der Audiopuffer, sofern verfügbar, oder aus aggregierten Pegeln).
- **Verarbeitung:** Die Funktion `_fft_to_log_bands()` mappt FFT-Magnituden auf **logarithmisch verteilte Bänder** (typisch für Spektrum-Anzeigen: mehr Bänder im Bass, weniger im Hochton).
- **Darstellung:** 24 Balken, unten Grün, darüber Gelb, oben Rot, mit **Peak-Hold** (Balken bleiben kurz auf Maximalwert).

Damit ist es eine **Frequenz-vs.-Amplitude-Anzeige** im Stil eines Spektrumanalysators, nur als Balken statt durchgezogene Kurve.

---

## Loudness-Taste (technisch umsetzbar?)

**Ja.** Eine Loudness-Funktion ist technisch umsetzbar, sowohl rein per Software als auch mit GStreamer:

1. **Wirkung:** Bei leiser Lautstärke werden Bass (und optional Höhen) angehoben, damit der Klang „voller“ wirkt (Fletcher-Munson-Kurven / Loudness-Compensation).

2. **Mögliche Umsetzung:**
   - **GStreamer:** Element `equalizer-3bands` (z. B. aus gst-plugins-good) mit `band0` (Bass) und ggf. `band2` (Höhen). Die Bänder werden abhängig von der eingestellten Lautstärke gesetzt (stärkerer Boost bei niedriger Lautstärke).
   - **Pipeline:** `playbin` erlaubt ein `audio-filter`; darin kann eine **Bin** aus `level` + `equalizer-3bands` verwendet werden. Bei Lautstärkeänderung: `volume`-Element anpassen und gleichzeitig Equalizer-Banden abhängig vom linearen Pegel setzen (z. B. bei 50 % Lautstärke +3 dB Bass, bei 25 % +6 dB).
   - **Einfachere Variante:** Nur eine nichtlineare Lautstärkekurve (z. B. leichte Anhebung bei niedrigen Sliderwerten), ohne echten EQ – weniger aufwendig, aber weniger „echte“ Loudness.

3. **Voraussetzungen:** GStreamer-Plugin `equalizer` (z. B. `gstreamer1.0-plugins-good`) muss installiert sein. Die aktuelle Player-Implementierung (`gst_player.py`) müsste um eine optionale Equalizer-Bin und die Ansteuerung der Bänder abhängig von der Lautstärke erweitert werden.

---

## UI-Referenz (Metall-Look)

- **Ausschalter:** Runder Button mit Power-Symbol (⏻), metallischer Verlauf (brushed-metal-ähnlich), im Code als `_close_btn` umgesetzt.
- **Lautstärkeregler:** Vertikaler Schieber mit vertieft wirkender Nut und runder, metallisch wirkender Griff (Stylesheet).
- **Analog/Digital-Schalter:** Horizontaler Schieber mit pillenförmiger Nut und zylindrisch wirkendem Griff (D = Digital/LED, A = Analog).
- **Grundplatte:** Zentrales Widget mit dunkelgrauem/schwarzem Metallverlauf; Anzeigebereich mit hellem Rand und abgerundeten Ecken für „unter Glas“-Optik.

Freie Icon-/Grafikquellen (optional für spätere Bild-Assets):

- Power-Switch: SVG Repo (CC0), Icons8, Freepik (Lizenz prüfen).
- Slider/Knob: Vecteezy, PNGTree, Icons8 (PNG/SVG).
- Metall-Texturen: z. B. CC0-Texturen (z. B. auf OpenGameArt, Pixabay) für Hintergrund; aktuell nur per Stylesheet-Gradienten umgesetzt.
