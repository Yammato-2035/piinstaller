# Icon-System (Lucide Static)

Alle UI-Icons der Snippets kommen aus **einer Quelle**: [Lucide](https://lucide.dev/), eingebunden als lokale SVGs unter `assets/icons/lucide/` (Paket **lucide-static** v0.460.0, Lizenz **ISC**).

## Verwendung in Snippets

- `{{LUCIDE:icon-name}}` — Standardgröße **48 px** (Kacheln, Karten).
- `{{LUCIDE:icon-name:72}}` — z. B. Mastheads (`masthead-mini__art`) oder größere Marken.

Die Ersetzung erfolgt in PHP (`setuphelfer_expand_lucide_placeholders`) vor dem URL-Rewrite der Snippets.

## Einheitliche Darstellung

- **Stroke:** `stroke-width="2"` im `viewBox 0 0 24 24` (normalisiert in `setuphelfer_lucide_icon()`).
- **Farbe:** `stroke="currentColor"`, Standardfarbe über CSS `.lucide-icon { color: var(--petrol); }`.
- **Kachelgröße:** Inhalt **48×48 px** in einer **72×72 px**-Box (`.icon-tile`); Startseite große Kacheln **96×96** mit ebenfalls **48 px** Icon.

## Neue Icons

1. Passende Datei von jsDelivr holen, z. B.  
   `https://cdn.jsdelivr.net/npm/lucide-static@0.460.0/icons/NAME.svg`
2. Nach `assets/icons/lucide/NAME.svg` legen.
3. Im Snippet `{{LUCIDE:NAME}}` verwenden.

Branding (Logo, Favicon) bleibt unter `assets/branding/` und ist kein Lucide-Icon.
