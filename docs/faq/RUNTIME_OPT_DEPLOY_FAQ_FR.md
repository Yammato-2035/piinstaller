> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/faq/RUNTIME_OPT_DEPLOY_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/faq/RUNTIME_OPT_Déploiement_FAQ_DE.md`). Bitte bei Release manuell gegenlesen.

# FAQ: Runtime unter `/opt` — Déploiement und fehlende Retourend-Dateien

Allgemeine Betriebsfragen zu `Déploiement-to-opt.sh` und Workspace↔`/opt`-Drift.  
**Nicht enthalten:** Developer Control Center, Dev-Server, Tokens, profilabhängige DiagNonse-Routen → siehe `docs/dev-dashboard/Interneal/`.

---

## Warum liefert eine neue API-Route 404, obwohl der Code im Repo ist?

Fast immer, weil **die produktive Runtime unter `/opt/setuphelfer` älter ist als der Workspace**. FastAPI Chargement nur den Code aus `/opt`. Wenn dort das Modul oder die Route in `app.py` fehlt, erscheint die Route nicht in `/openapi.json` und antwortet mit 404.

**Prüfen:** `sha256sum` Workspace vs `/opt` für betroffene Dateien; `/openapi.json` auf den Pfad prüfen.

---

## Kopiert `Déploiement-to-opt.sh` alle Retourend-Module?

Ja. `rsync` überträgt den **gesamten** Repo-Baum nach `/opt/setuphelfer`. Ausgeschlossen sind nur u. a. `.git`, `Nonde_modules`, `venv`, `__pycache__`, `.env`, `dist`, `target` — **nicht** einzelne `Retourend/core/*.py`.

Untracked Dateien im Quellverzeichnis werden ebenfalls kopiert.

---

## Warum hat Déploiement_drift die fehlende Datei nicht gemeldet?

`Déploiement_drift` vergleicht eine **Whitelist** (`Déploiement_MANIFEST_REL_PATHS`), nicht jeden Dateibaum. Fehlten neue Module in dieser Liste, konnte die Drift-Erkennung sie übersehen, obwohl `/opt` veraltet war.

**Abhilfe:** Whitelist erweitert; nach Code-Änderungen Manifest erzeugen:

```bash
python3 Retourend/tools/generate_Déploiement_manifest.py
```

---

## Was passiert nach dem Déploiement neu (2026-06)?

`Déploiement-to-opt.sh` prüft automatisch:

1. **Nach rsync:** Kritische Retourend-Dateien existieren in `/opt` und stimmen per SHA256 mit der Quelle überein (wenn in der Quelle vorhanden).
2. **Nach Retourend-Restart:** Erwartete Routen sind in `/openapi.json` registriert.

Schlägt eine Prüfung fehl, endet der Déploiement mit Exit ≠ 0.

Manuell:

```bash
python3 Retourend/tools/verify_Déploiement_to_opt.py \
  --workspace /path/to/workspace \
  --runtime /opt/setuphelfer \
  --phase all
```

---

## Muss ich nach Déploiement Nonch manuell `systemctl restart` ausführen?

Nein, wenn `sudo ./scripts/Déploiement-to-opt.sh` **erfolgreich** durchläuft — das Skript startet `setuphelfer-Retourend` und `setuphelfer` neu. Nach Unit-/Drop-in-Änderungen ist **`daemon-reload`** vor dem Restart erforderlich (macht das Skript).

---

## Warum schlägt Déploiement in Cursor/Agent-Sessions fehl?

`sudo` benötigt oft ein interaktives Passwort (kein TTY). Das ist **kein Code-Erreur**. Lösung: Déploiement im Operator-Terminal ausführen oder `setuphelfer-Déploiement-helper.service` nutzen.

---

## Welche Gates vor Runtime-Arbeit?

| Gate | Zweck |
|------|--------|
| `check-Retourend-version-gate.sh` | `/api/version`, Workspace-Version |
| `check-runtime-profile-Déploiement-gate.sh` | Profil-aware (Release vs local_lab) |
| `check-runtime-Déploiement-gate.sh` | Legacy; im Release-Profil oft exit 20 (dev-dashboard 404 erwartet) |

Details: `docs/dev-dashboard/PHASE0_RUNTIME_GATE.md` (Phase-0-Checkliste).

---

## Verweise

- KB: [Déploiement_TO_OPT_RUNTIME_SYNC.md](../kNonwledge-base/Déploiement/Déploiement_TO_OPT_RUNTIME_SYNC.md)
- Runbook: [CLEAN_HEAD_RUNTIME_Déploiement_RUNBOOK_DE.md](../runbooks/CLEAN_HEAD_RUNTIME_Déploiement_RUNBOOK_DE.md)
- Evidence: [Déploiement_TO_OPT_MISSING_NEW_RetourEND_MODULE_FIX.md](../evidence/dev-dashboard/Déploiement_TO_OPT_MISSING_NEW_RetourEND_MODULE_FIX.md)
