# Setuphelfer Development Server — MVP-Architektur

## 1. Zweck

Der **Setuphelfer Development Server** ist ein lokaler, dev-only Dienst zur Entwicklungsbeschleunigung:

- **Labor-/Testhardware verwalten** — VMs, physische Maschinen, Raspberry Pi, Rettungsstick Developer Edition
- **Strukturierte Systemberichte empfangen** — Inventory, Boot, Storage, Backup-Preflight, Rescue, SSH-Probe
- **Developer-Rettungsstick-Daten empfangen** — automatisch im lokalen Lab (Developer Edition)
- **SSH-read-only-Diagnostik vorbereiten** — Allowlist-Profile, keine freien Shell-Befehle
- **Dashboard-Anzeige** — Remote-Rechner im Development Cockpit sichtbar machen
- **Prompt-/Runbook-Kandidaten erzeugen** — Entwürfe aus gesammelten Befunden (Stub im MVP)

Öffentliche Rettungssticks senden **nie** automatisch Daten. Public/Beta-Modus arbeitet nur mit explizitem Opt-in und redigiertem Auszug.

## 2. Modi

| Modus                | Zweck                         | Automatischer Upload | SSH                  | Datenschutz                        |
| -------------------- | ----------------------------- | -------------------- | -------------------- | ---------------------------------- |
| public_rescue        | normaler Nutzer-Rettungsstick | nein                 | nein                 | maximale Datensparsamkeit          |
| beta_opt_in          | freiwilliger Auszug           | nur explizit         | nein                 | redigiert/anonymisiert             |
| local_lab            | eigene Testhardware           | ja, lokal            | read-only erlaubt    | intern, aber Redaction vorbereiten |
| dangerous_lab_future | spätere Schreibtests          | nur lokal            | nur nach Backup/Gate | nicht in diesem MVP                |

## 3. Sicherheitsprinzipien

- Public Builds senden **nicht** automatisch.
- Lab Builds senden nur an den konfigurierten lokalen Dev-Server (`127.0.0.1`).
- SSH-Kommandos nur über **Allowlist-Profile** — kein Shell-Freitext.
- Kein `sudo`, kein write/mount/umount/dd/mkfs/parted/sfdisk/sgdisk/wipefs.
- Jede Aktion wird als **Audit-Event** protokolliert (`dev_server_events.jsonl`).
- Dashboard zeigt live, was auf welchem Rechner passiert.
- Spätere Schreibentscheidungen nur nach Backup-/Evidence-Gates.

## 4. Trennung der Datenklassen

| Klasse                 | Beschreibung                                      |
| ---------------------- | ------------------------------------------------- |
| raw_lab_data           | Vollständige Lab-Berichte (nur `local_lab`)       |
| redacted_beta_extract  | Gehashte/redigierte Felder für Beta-Opt-in        |
| public_safe_summary    | Minimale Zusammenfassung für Public               |
| evidence_reference     | Pfade zu Evidence-Artefakten im Repo              |
| prompt_candidate       | Entwürfe für Cursor-Prompts / Runbooks            |

## 5. Spätere Ausbaustufen

- Signed runbooks
- Adaptive rescue profiles
- Backup-gated remote actions
- Hardware compatibility matrix
- Prompt generator (KI-gestützt)
- FAQ/KB/i18n candidate generator

## 6. Implementierung (MVP)

- Backend-Modul: `backend/devserver/`
- Persistenz: `docs/evidence/runtime-results/dev-server/`
- API-Präfix: `/api/dev-server/`
- Default: **disabled** (`SETUPHELFER_DEV_SERVER_ENABLED=false`)
- Router-Registrierung: minimal in `backend/app.py`

Siehe auch: `docs/evidence/dev-server/DEV_SERVER_MVP_IMPLEMENTATION.md`
