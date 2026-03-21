# Version 1.3.8.2 — Prüfliste 5

## Prüfung

```text
rg '1\.0\.0' website/setuphelfer-theme → keine Treffer
```

## Relevante Stellen

- `snippets/download.html`, `snippets/changelog.html`
- `functions.php` — `wp_enqueue_*` Version, JSON-LD `softwareVersion`
- `style.css`, `setuphelfer-child/style.css`, `setuphelfer-child/functions.php`

**Ergebnis:** Konsistent **1.3.8.2**.
