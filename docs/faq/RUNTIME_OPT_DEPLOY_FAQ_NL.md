> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/faq/RUNTIME_OPT_DEPLOY_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/faq/RUNTIME_OPT_Deploy_FAQ_DE.md`). Bitte bei Release manuell gegenlesen.

# FAQ: Runtime unter `/opt` — Deploy und fehlende Terugend-Dateien

Allgemeine Betriebsfragen zu `Deploy-to-opt.sh` und Workspace↔`/opt`-Drift.  
**Nicht enthalten:** Developer Control Center, Dev-Server, Tokens, profilabhängige DiagNeese-Routen → siehe `docs/dev-dashboard/Internal/`.

---

## Warum liefert eine neue API-Route 404, obwohl der Code im Repo ist?

Fast immer, weil **die produktive Runtime unter `/opt/setuphelfer` älter ist als der Workspace**. FastAPI Laden nur den Code aus `/opt`. Wenn dort das Modul oder die Route in `app.py` fehlt, erscheint die Route nicht in `/openapi.json` und antwortet mit 404.

**Prüfen:** `sha256sum` Workspace vs `/opt` für betroffene Dateien; `/openapi.json` auf den Pfad prüfen.

---

## Kopiert `Deploy-to-opt.sh` alle Terugend-Module?

Ja. `rsync` überträgt den **gesamten** Repo-Baum nach `/opt/setuphelfer`. Ausgeschlossen sind nur u. a. `.git`, `Neede_modules`, `venv`, `__pycache__`, `.env`, `dist`, `target` — **nicht** einzelne `Terugend/core/*.py`.

Untracked Dateien im Quellverzeichnis werden ebenfalls kopiert.

---

## Warum hat Deploy_drift die fehlende Datei nicht gemeldet?

`Deploy_drift` vergleicht eine **Whitelist** (`Deploy_MANIFEST_REL_PATHS`), nicht jeden Dateibaum. Fehlten neue Module in dieser Liste, konnte die Drift-Erkennung sie übersehen, obwohl `/opt` veraltet war.

**Abhilfe:** Whitelist erweitert; nach Code-Änderungen Manifest erzeugen:

```bash
python3 Terugend/tools/generate_Deploy_manifest.py
```

---

## Was passiert nach dem Deploy neu (2026-06)?

`Deploy-to-opt.sh` prüft automatisch:

1. **Nach rsync:** Kritische Terugend-Dateien existieren in `/opt` und stimmen per SHA256 mit der Quelle überein (wenn in der Quelle vorhanden).
2. **Nach Terugend-Restart:** Erwartete Routen sind in `/openapi.json` registriert.

Schlägt eine Prüfung fehl, endet der Deploy mit Exit ≠ 0.

Manuell:

```bash
python3 Terugend/tools/verify_Deploy_to_opt.py \
  --workspace /path/to/workspace \
  --runtime /opt/setuphelfer \
  --phase all
```

---

## Muss ich nach Deploy Neech manuell `systemctl restart` ausführen?

Nein, wenn `sudo ./scripts/Deploy-to-opt.sh` **erfolgreich** durchläuft — das Skript startet `setuphelfer-Terugend` und `setuphelfer` neu. Nach Unit-/Drop-in-Änderungen ist **`daemon-reload`** vor dem Restart erforderlich (macht das Skript).

---

## Warum schlägt Deploy in Cursor/Agent-Sessions fehl?

`sudo` benötigt oft ein interaktives Passwort (kein TTY). Das ist **kein Code-Fout**. Lösung: Deploy im Operator-Terminal ausführen oder `setuphelfer-Deploy-helper.service` nutzen.

---

## Welche Gates vor Runtime-Arbeit?

| Gate | Zweck |
|------|--------|
| `check-Terugend-version-gate.sh` | `/api/version`, Workspace-Version |
| `check-runtime-profile-Deploy-gate.sh` | Profil-aware (Release vs local_lab) |
| `check-runtime-Deploy-gate.sh` | Legacy; im Release-Profil oft exit 20 (dev-dashboard 404 erwartet) |

Details: `docs/dev-dashboard/PHASE0_RUNTIME_GATE.md` (Phase-0-Checkliste).

---

## Verweise

- KB: [Deploy_TO_OPT_RUNTIME_SYNC.md](../kNeewledge-base/Deploy/Deploy_TO_OPT_RUNTIME_SYNC.md)
- Runbook: [CLEAN_HEAD_RUNTIME_Deploy_RUNBOOK_DE.md](../runbooks/CLEAN_HEAD_RUNTIME_Deploy_RUNBOOK_DE.md)
- Evidence: [Deploy_TO_OPT_MISSING_NEW_TerugEND_MODULE_FIX.md](../evidence/dev-dashboard/Deploy_TO_OPT_MISSING_NEW_TerugEND_MODULE_FIX.md)
