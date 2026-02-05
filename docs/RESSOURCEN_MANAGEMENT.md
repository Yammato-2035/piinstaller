# Ressourcen-Management (Milestone 3 – Transformationsplan)

Pi-spezifische Optimierungen und Hinweise für Einsteiger.

## Ziele

- **GPU-Speicher:** Automatisch anpassen (z. B. für Video-Decoding).
- **Swap:** Bei RAM < 2 GB Swap empfehlen bzw. einrichten.
- **Temperatur:** Warnung bei > 80°C (Kühlung prüfen).
- **App-Installation:** „Diese App benötigt 1 GB RAM – dein Pi hat 4 GB“ und „Leichtgewichtige Alternative“ vorschlagen.

## Umsetzung im PI-Installer

### API `/api/system/resources`

- **ram_total_gb:** Gesamt-RAM in GB (für App-Store-Hinweise).
- **swap_total_mb / swap_used_mb:** Swap-Status.
- **temperature_c:** CPU-Temperatur.
- **temperature_warning:** `true` wenn ≥ 80°C.
- **swap_recommended:** `true` wenn RAM < 2 GB.

### Dashboard

- Im Hero-Bereich: Ressourcen-Ampel (CPU/RAM/Speicher).
- Wenn Temperatur ≥ 80°C: Hinweis „Temperatur hoch – Kühlung prüfen“.
- Wenn RAM < 2 GB: Hinweis „Swap wird empfohlen“.

### App-Store (geplant)

- Bei jeder App: Anzeige „Benötigt ca. X MB RAM“ bzw. „Empfohlen: 1 GB RAM“.
- Wenn `ram_total_gb` kleiner als Empfehlung: Hinweis „Dein Pi hat X GB RAM – App kann langsam laufen“ und ggf. leichte Alternative nennen.

### Swap einrichten (manuell / Doku)

- **Raspberry Pi OS:** Swap ist oft vorkonfiguriert (z. B. 100 MB). Bei wenig RAM: Swap vergrößern (z. B. 1 GB) oder `dphys-swapfile` anpassen.
- **Anleitung:** Siehe **PI_OPTIMIZATION.md** oder Raspberry Pi Dokumentation.

### Temperatur

- **Normal:** 40–70°C unter Last.
- **Warnung:** ≥ 80°C – Kühlkörper/Lüfter prüfen, Last reduzieren.
- **vcgencmd:** Auf dem Pi: `vcgencmd measure_temp`.

## Siehe auch

- **PI_OPTIMIZATION.md** – Pi-Optimierung
- **Dashboard** – Ressourcen-Ampel und Hinweise
- **TRANSFORMATIONSPLAN.md** – Phase 4.2 Ressourcen-Management
