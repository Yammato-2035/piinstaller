# Plesk Free Version — Zukunftsplan

**Stand:** 2026-06-16  
**Status:** **Zukunft / nicht implementiert** — kein Build, kein Live-Deploy aus dem Public-Repo

---

## Einordnung

**Plesk Free** bezeichnet eine geplante Hosting-/Panel-Integration im Setuphelfer-Ökosystem. Sie ist **kein** Bestandteil des aktuellen Recovery-Core (Backup, Restore, Rettungsstick) und wird **erst nach** Reife von Cloudserver Edition und Operator-Infrastruktur angegangen.

---

## Was im Public-Repo erlaubt ist

- Roadmap- und Grenzdokumentation (diese Datei)
- Handoff-Beschreibung ohne Implementierung
- FAQ-Verweise auf „geplant / nicht verfügbar“

---

## Was verboten ist (Public-Repo)

- Plesk-API-Integration mit echten Tokens
- Katalog-Submission-Secrets (`PLESK_CATALOG_SUBMISSION_SECRET` — Gate-blockiert)
- Produktions-Deploy-Skripte für Plesk-Marketplace
- Implementierung einer „kostenlosen Plesk-Edition“ als lauffähiges Modul

---

## Abhängigkeiten (logisch)

```text
Recovery-Core (grün)  →  Cloudserver Edition (private)  →  Operator/Billing (private)  →  Plesk Free (Zukunft)
```

Keine Parallel-Priorisierung laut Roadmap-Registry.

---

## Private-Repo (wenn freigegeben)

- Hosting-Provider-Adapter
- Lizenz-/Feature-Kopplung mit `setuphelfer.operator_private`
- Eigene CI/CD und Secrets-Verwaltung

Handoff: [`docs/private-handoff/PLESK_FREE_VERSION_FUTURE_HANDOFF.md`](../private-handoff/PLESK_FREE_VERSION_FUTURE_HANDOFF.md)

---

## Kommunikation nach außen

Website und Public-Doku dürfen Plesk Free nur als **„geplant“** oder **„in Evaluierung“** bezeichnen — nicht als verfügbares Produkt.

---

## FAQ

[`docs/faq/CLOUDSERVER_BOUNDARY_FAQ_DE.md`](../faq/CLOUDSERVER_BOUNDARY_FAQ_DE.md) (Abschnitt Plesk Free)
