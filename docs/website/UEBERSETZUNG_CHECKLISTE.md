# Übersetzungs-Checkliste (DE / EN)

**Legende:** `[ ]` offen · `[x]` erledigt (bitte nur auf `[x]` setzen, wenn **alle** Unterpunkte für diesen Block wirklich übersetzt sind).

**Stand:** wird bei Arbeit an i18n aktualisiert. Website-Locale: `?lang=en` oder Cookie. App-Locale: Einstellungen → Sprache.

---

## A. WordPress-Theme (Chrome)

| Element | DE | EN | Status |
|--------|----|----|--------|
| Header: Marken-Tagline | ✓ | ✓ | `[x]` |
| Header: Sprachschalter DE \| EN | ✓ | ✓ | `[x]` |
| Header: „Menü“ (Mobile) | ✓ | ✓ | `[x]` |
| Header: Suche (Label, Placeholder, Button) | ✓ | ✓ | `[x]` |
| **Hauptnavigation (WP-Menü „primary“)** | ✓ | ✓ | `[x]` (Filter `nav_menu_item_title` + URL-Slug) |
| Fallback-Menü (ohne WP-Menü) | ✓ | ✓ | `[x]` |
| Footer: drei Spalten (Labels + Links) | ✓ | ✓ | `[x]` |
| Footer: Markenhinweis (lang) | ✓ | ✓ | `[x]` |
| Consent-Banner | ✓ | ✓ | `[x]` |
| `html lang`-Attribut | ✓ | ✓ | `[x]` |
| SEO `pre_get_document_title` / Meta-Description bei `lang=en` | — | ✓ | `[x]` (Kernseiten + Dokumentation) |

---

## B. Theme-Snippets (`snippets/*.html` → bei EN: `snippets/en/<name>.html`)

Vorhandene Snippets (ohne `en/` = bei EN meist **deutscher Fallback**).

| Datei | DE-Inhalt | `snippets/en/…` | Status |
|-------|-----------|-------------------|--------|
| `index.html` | ✓ | `en/index.html` | `[x]` |
| `about.html` | ✓ | `en/about.html` | `[x]` |
| `changelog.html` | ✓ | — | `[ ]` |
| `kontakt.html` | ✓ | — | `[ ]` |
| `sicherheit.html` | ✓ | — | `[ ]` |
| `download.html` | ✓ | — | `[ ]` |
| `community.html` | ✓ | — | `[ ]` |
| `documentation.html` | ✓ | `en/documentation.html` | `[x]` |
| `projects.html` | ✓ | — | `[ ]` |
| `tutorials.html` | ✓ | — | `[ ]` |
| `troubleshooting.html` | ✓ | — | `[ ]` |
| `guided-start.html` | ✓ | — | `[ ]` |
| `cookie-policy.html` | ✓ | — | `[ ]` |
| `tutorial-*.html` (11 Dateien) | ✓ | — | `[ ]` |
| `project-*.html` (7 Dateien) | ✓ | — | `[ ]` |
| `doc-*.html` (Hauptkapitel in `setuphelfer_docs()`) | ✓ | `en/doc-*.html` (5 Dateien) | `[x]` |
| `issue-*.html` (6 Dateien) | ✓ | — | `[ ]` |

**Gesamt Snippets:** 47 Dateien · **mit EN-Version:** 4+ (u. a. index, about, documentation, doc-*) · **offen:** siehe Tabelle

---

## C. WordPress-Inhalte (Datenbank)

| Bereich | DE | EN | Status |
|---------|----|----|--------|
| Seiten (Impressum, Datenschutz, …) | ✓ | — | `[ ]` (ggf. englische Seiten oder WPML/Polylang) |
| Beiträge `projekt`, `tutorial`, `fehlerhilfe`, `doc_entry` | ✓ | — | `[ ]` |
| bbPress / Foren (falls aktiv) | ? | ? | `[ ]` |

---

## D. Desktop-App (`frontend/`, Locale `de.json` / `en.json`)

### D.1 Kern / global

| Bereich | Status |
|---------|--------|
| `i18n/index.ts`, `main.tsx`, Error-Boundary | `[x]` |
| `Sidebar`, `PlatformContext`, Risiko-Labels | `[x]` |
| `App.tsx` (Screenshots, Mobile) | `[x]` |
| `SettingsPage` → Sprachwahl | `[x]` (weitere Untertabs teils DE) |

### D.2 Seiten (`src/pages/*.tsx`)

| Datei | Status |
|-------|--------|
| `Dashboard.tsx` | `[x]` (laufend prüfen) |
| `FirstRunWizard.tsx` (Komponente) | `[x]` |
| `Documentation.tsx` | `[ ]` (Navigation/teils EN; Kapiteltexte größtenteils DE) |
| `SettingsPage.tsx` | `[ ]` (viele Unterbereiche noch DE) |
| `SecuritySetup.tsx` | `[ ]` |
| `MailServerSetup.tsx` | `[x]` (prüfen auf Reststrings) |
| `BackupRestore.tsx` | `[ ]` |
| `ControlCenter.tsx` | `[ ]` |
| `MonitoringDashboard.tsx` | `[ ]` |
| `AppStore.tsx` | `[ ]` |
| `InstallationWizard.tsx` | `[ ]` |
| `PresetsSetup.tsx` | `[ ]` |
| `UserManagement.tsx` | `[ ]` |
| `WebServerSetup.tsx` | `[ ]` |
| `NASSetup.tsx` | `[ ]` |
| `HomeAutomationSetup.tsx` | `[ ]` |
| `MusicBoxSetup.tsx` | `[ ]` |
| `KinoStreaming.tsx` | `[ ]` |
| `LearningComputerSetup.tsx` | `[ ]` |
| `DevelopmentEnv.tsx` | `[ ]` |
| `PeripheryScan.tsx` | `[ ]` |
| `RaspberryPiConfig.tsx` | `[ ]` |
| `PiInstallerUpdate.tsx` | `[ ]` |
| `TFTPage.tsx` | `[ ]` |
| `DsiRadioSettings.tsx` | `[ ]` |

### D.3 Komponenten / Features

| Datei / Ordner | Status |
|----------------|--------|
| `SudoPasswordDialog.tsx`, `SudoPasswordModal.tsx` | `[x]` |
| `RunningBackupModal.tsx`, `HelpTooltip.tsx` | `[x]` |
| `RadioPlayer.tsx` | `[x]` |
| `features/remote/**` | `[ ]` |
| Sonstige Komponenten | `[ ]` (stichprobenartig) |

### D.4 Backend (nutzerlesbare Meldungen)

| Bereich | Status |
|---------|--------|
| `backend/app.py` API-Titel | `[x]` (Produktname) |
| JSON-Fehlermeldungen / Presets-Texte | `[ ]` |

---

## E. Abschlusskriterium „Website EN vollständig“

- [ ] Alle Zeilen unter **B** und relevante Punkte unter **C** auf `[x]`.
- [ ] Menüpunkte im WP-Backend getestet (abweichende Titel ggf. in `setuphelfer_nav_menu_item_title_i18n` ergänzen).

## F. Abschlusskriterium „App EN vollständig“

- [ ] Alle Zeilen unter **D.2–D.4** auf `[x]`.
- [ ] `npm run build` ohne Fehler; manuell Sprache EN durchklicken.

---

*Diese Datei ist die verbindliche Checkliste für den Übersetzungsstand. Einträge nur auf `[x]` setzen, wenn der jeweilige Block vollständig übersetzt ist.*
