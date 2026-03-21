# Community — Prüfliste 3

## Technik

| Punkt | Ergebnis |
|-------|----------|
| `page-community.php` | Nutzt `setuphelfer_render_snippet('community')` — **keine** rohen `{{LUCIDE:…}}` in der Ausgabe. |
| Masthead | `snippets/community.html` — **Foto** statt Lucide-Hauptmotiv (`masthead-mini--photo`). |

## Prüfung

| Frage | Ergebnis |
|-------|----------|
| Template-Tokens sichtbar im Browser? | **Nein** (bei PHP-Rendering). |
| Community-Hero leer? | **Nein** — `community-hero-real-setup.jpg`. |
