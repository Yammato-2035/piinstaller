# WordPress: englische Texte & Menüs (Import-Hilfe)

Die **Seiteninhalte** der SetupHelfer-Website kommen überwiegend aus **Theme-Snippets** (`website/setuphelfer-theme/snippets/` und bei `?lang=en` aus `snippets/en/`). In der Datenbank sind viele Seiten **absichtlich leer** — der Text liegt im Theme, nicht im Editor.

## Dateien in diesem Ordner

| Datei | Zweck |
|--------|--------|
| `setuphelfer-en-strings.csv` | Tabellarische Referenz: Menü-/Seitenbezeichnungen und Dokumentations-Titel (EN). Keine Übersetzung von URLs oder Code — nur Beschriftungen. |
| `setuphelfer-wordpress-en-bundle.json` | Maschinenlesbar dieselben Daten (z. B. für Skripte oder manuelles Abgleichen). |

## Was du in WordPress tun musst (kurz)

1. **Permalink der About-Seite:** soll **`ueber-setuphelfer`** sein (oder nutze die Aliasse `ueber` / `about` im Theme — ab Theme-Version mit `page.php`-Mapping). Wenn die Seite z. B. nur `ueber` heißt, war der Inhalt leer, weil das Snippet nicht gemappt war.
2. **Sprache:** `?lang=en` oder Cookie `setuphelfer_lang=en` — dann werden vorhandene `snippets/en/*.html` geladen.
3. **Hauptmenü:** Bei `lang=en` übersetzt das Theme die **Anzeige** der Menüeinträge per Filter (`inc/setuphelfer-i18n.php`). Die **gespeicherten** Menütitel in WP können deutsch bleiben.
4. **Dokumentation (CPT `doc_entry`):** Fließtext kommt aus Snippets; englische Archive-/Detailtexte liegen unter `snippets/en/documentation.html` und `snippets/en/doc-*.html`.

## Kein klassisches „Übersetzungs-Upload“ nötig

Ein natives WordPress-WXR-Importfile ersetzt **keine** Snippet-Dateien. Für fehlende EN-Texte: Snippets im Repo pflegen und Theme deployen. Die CSV/JSON hier dienen der **Abstimmung** mit Redaktion/Hosting und als Checkliste.

## Tauri-Screenshots (englische UI)

Dokumentations-Screenshots sollen die **englische App-Oberfläche** zeigen. In der Desktop-App (Dashboard → Dokumentations-Screenshot-Karte) wird die UI für den Lauf **kurz auf Englisch** umgestellt; Ausgabe: `Dokumente/SetupHelfer/docs/screenshots/` (Bilder bei Bedarf ins Theme nach `assets/screenshots/` kopieren).
