# Security Review: SettingsPage

## Kurzbeschreibung

Einstellungen: Theme, Erfahrungsstufe (beginner/advanced/developer), ggf. API /api/settings (get/post). Keine privilegierten Aktionen.

## Angriffsfläche

Eingaben: experienceLevel, Theme. Backend: settings lesen/schreiben (nicht systemkritisch).

## Ampelstatus

**GRÜN.** Betroffene Dateien: frontend/src/pages/SettingsPage.tsx, backend/app.py /api/settings.
