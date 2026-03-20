# Phase 2 – Branding-System festgezogen (setuphelfer.de)

Datum: 2026-03-17
Vorgehen: Bestehende Vorlagen genutzt, keine freie Neuerfindung.

## 1) Ziel der Phase

Ein verbindliches Mini-Branding-System definieren und technisch verankern, damit Header, kleine Flaechen, Icon-Einsatz und Favicons konsistent zur Produktwelt von Setuphelfer / PI-Installer auftreten.

## 2) Ausgewaehlte Logo-/Branding-Versionen

Auf Basis der vorhandenen Logo-Vorlage (`logo-app.svg` / `logo-symbol.svg`, identischer Inhalt) wurde eine klare Rollenverteilung angelegt:

- Hauptlogo (Header/Website):
  - `assets/branding/setuphelfer-logo-main.svg`
- Kompakte Wortmarke:
  - `assets/branding/setuphelfer-wordmark-compact.svg`
- Symbol/Signet:
  - `assets/branding/setuphelfer-signet.svg`
- Favicon:
  - `assets/branding/setuphelfer-favicon.svg`
- App-nahes Icon (Download/Hero/Social):
  - `assets/branding/setuphelfer-app-icon.svg`

Hinweis: Fuer Hauptlogo/Signet/Favicon/App-Icon wurde bewusst dieselbe bestehende Markenform als technische Rollenaufteilung verwendet, um sofortige Konsistenz zu erreichen und keine Stilbrueche einzufuehren.

## 3) Technische Umsetzung im Theme

- Header-Logo umgestellt auf:
  - `assets/branding/setuphelfer-logo-main.svg`
- Favicon im `head` gesetzt:
  - `rel="icon"` -> `assets/branding/setuphelfer-favicon.svg`
  - `rel="apple-touch-icon"` -> `assets/branding/setuphelfer-app-icon.svg`
- Asset-Mapping erweitert:
  - Branding-Block in `website/setuphelfer-theme/ASSET_MAPPING.md`

## 4) Verbindliche Einsatzregeln (ab jetzt)

- Header und globale Markenflaechen:
  - nur `setuphelfer-logo-main.svg`
- Kleine Flaechen / kompakte Darstellungen:
  - `setuphelfer-signet.svg`
- Browser-Icon:
  - `setuphelfer-favicon.svg`
- App-nahe Darstellung in Produktkontext (Download/Hero/Social):
  - `setuphelfer-app-icon.svg`
- Textdominante Enge (falls noetig):
  - `setuphelfer-wordmark-compact.svg`

## 5) Abgrenzung zu naechsten Phasen

Diese Phase hat nur Branding-Rollen und technische Verankerung abgeschlossen.
Noch offen (bewusst nicht vorgezogen):

- Hero-Rebuild mit staerkerer Produktwirkung (Phase 3)
- Echte Build-Screenshots und Einbindung (Phase 4)
- Farbangleichung an PI-Installer (Phase 7)
- Icon-Qualitaetsangleichung im Gesamtbild (spaetere Phase)

## 6) Selbstpruefung Phase 2

- Bestehende gute Vorlagen genutzt statt freie Neuentwicklung: Ja.
- Keine unnötigen Design-Experimente: Ja.
- Rollenmodell fuer Logo-System verbindlich definiert: Ja.
- Technisch im Theme verankert (Header/Favicon): Ja.
- Kompatibel mit weiterer produktnaher Ausrichtung: Ja.

