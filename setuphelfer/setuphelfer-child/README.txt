SetupHelfer Child Theme
=======================

Dieses Verzeichnis enthält ein Child-Theme für das bestehende Theme `setuphelfer`.

Zweck
-----
Alle wesentlichen Funktionen und Templates bleiben im Parent-Theme.
Child-Theme enthält nur gezielte Overrides und einen sauberen Einstieg für zukünftige CSS/Template-Anpassungen.

Parent-Theme
-------------
Ordner (auf dem Server): `wp-content/themes/setuphelfer`

Child-Theme
------------
Ordner (auf dem Server): `wp-content/themes/setuphelfer-child`

Wichtige Dateien
------------------
- Parent (setuphelfer):
  - `functions.php`: Theme-Logik, Post Types, Seed-Funktionen, Header/Footer/Templates
  - `page-community.php`: existiert weiterhin im Parent (wird durch Child überschrieben, sobald Child aktiviert ist)
- Child (setuphelfer-child):
  - `style.css`: Theme-Header mit `Template: setuphelfer`
  - `functions.php`: lädt Child-Styles (aktuell noch ohne zusätzliche CSS-Regeln)
  - `page-community.php`: Template-Override (Intro-Snippet + bbPress-Forum)

Später leicht wartbar anpassen
--------------------------------
1. CSS: ergänze Regeln in `setuphelfer-child/style.css` (oder erweitere Child-Styles).
2. Templates: überschreibe nur die Templates, die wirklich abweichen sollen (z.B. `page-community.php`).

